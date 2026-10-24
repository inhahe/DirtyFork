# todo: test cycle detection with ConfigView, across different config inputs
# todo: we can handle option_defaults by assigning a merge or a configview to each option with first dict being a Config of (or can we just pass it directly?) option_defaults 
#       same with user_defaults and users
# i wonder if we could just do child = child | option_defaults   or child |= option_defaults?
# todo: provide a function to return a regular old dict of the Config or ConfigView object for passing to yaml.dump
# may have to do something similar for input_fields too. 
# test if we can use anchors across yaml files
# note that there's currently no way to distinguish between a value being defined as null and the value 
#  not existing.

import os
from collections import defaultdict
from collections.abc import Mapping, Iterable
from string import Formatter

import yaml, yaml_include

from definitions import *

yaml.add_constructor("!include", yaml_include.Constructor(base_dir=None), Loader=yaml.SafeLoader)

class Config(defaultdict):
    def __init__(self, source=None, *, _root=None, strict=True):
        super().__init__(lambda: null) 
        self._root = _root or self

        if _root is None:
          self._strict = strict
          self._resolving = set()  
        else:
          self._strict = _root._strict

        if source is None:
            return

        if isinstance(source, Mapping):
            for k, v in source.items():
                self[k] = self._wrap(v)
        else:
            for k, v in vars(source).items():
                self[k] = self._wrap(v)

    def __repr__(self):
        return dict.__repr__(self) # prevent the __init__ function from showing up when printing the dictionary's contents

    def __missing__(self, key):
        # A key not there reads as null and stays not there (defaultdict's
        # would add it: a key read once, as a {placeholder} is when it is
        # resolved, would then hide the layers below it in a ConfigView).
        return null

    def __getattr__(self, name):
        return self._get(name)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self[name] = self._wrap(value)

    def __delattr__(self, name):
        del self[name]

    def __iter__(self):
        """Iterate over values instead of keys to allow iterating over config objects."""
        for key in super().__iter__():
            yield self[key]

    def keys(self):
        """Return an iterator over the keys."""
        return super().__iter__()

    def values(self):
        """Return an iterator over the values (Config objects)."""
        for key in super().__iter__():
            yield self[key]

    def items(self):
        """Return an iterator over (key, value) pairs."""
        for key in super().__iter__():
            yield (key, self[key])

    # -----------------------------
    # Lazy resolution
    # -----------------------------

    def __getitem__(self, key):
        value = super().__getitem__(key)
        if getattr(self._root, '_resolving', null) is null:
            self._root._resolving = set()
        self._root._resolving.add(key)
        try:
             result = self._resolve(value)
             return null if result is None else result
        finally:
            self._root._resolving.discard(key)

    def _get(self, key, default=null):
        value = super().get(key, default)
        if value is null:
            return value
        if getattr(self._root, '_resolving', null) is null:
            self._root._resolving = set()
        self._root._resolving.add(key)
        try:
            result = self._resolve(value)
            return null if result is None else result
        finally:
            self._root._resolving.discard(key)
    
    def _wrap(self, value):
        if isinstance(value, Config):
            return value

        if isinstance(value, Mapping):
            return Config(value, _root=self._root)

        if hasattr(value, "__dict__") and not callable(value):
            return Config(vars(value), _root=self._root)

        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            return [self._wrap(v) for v in value]

        return value  
      
    def _resolve(self, value):
        if not isinstance(value, str):
            return value

        value = os.path.expandvars(value)

        if '{' not in value:
            return value

        formatter = _DotFormatter(
            strict=self._strict,
            resolving=self._root._resolving,
            root=self._root,
        )

        try:
            return formatter.format(value, self)
        except (ValueError, KeyError, IndexError):
            return value

    def merge(self, *sources, deep=True):
        """In-place merge."""
        def do_merge(target, source):
            items = source.items() if isinstance(source, Mapping) else vars(source).items()

            for k, v in items:
                if (
                    deep
                    and k in target
                    and isinstance(target[k], Config)
                    and isinstance(v, Mapping)
                ):
                    do_merge(target[k], v)
                else:
                    target[k] = target._wrap(v)

        for src in sources:
            do_merge(self, src)

        def fix_root(cfg):
            cfg._root = self
            for v in cfg.values():
                if isinstance(v, Config):
                    fix_root(v)

        fix_root(self)
        return self

    def extended(self, *sources, deep=True):
        new = Config(self, strict=self._root._strict)
        new.merge(*sources, deep=deep)
        return new

    # -----------------------------
    # Operators
    # -----------------------------

    def __or__(self, other):  # a = b | c
      return ConfigView(other, self)

    def __ior__(self, other): # a != b
      return self.merge(other)

    def shallow(self, *sources):
        return self.extended(*sources, deep=False)

class _DotFormatter(Formatter):
    
    def __init__(self, *, strict=True, resolving=None, root=None):
        self.strict = strict
        self.resolving = resolving if resolving is not None else set()
        self.root = root if root is not None else {}

    def get_field(self, field_name, args, kwargs):
        if field_name in self.resolving:
            raise ValueError(f"Interpolation cycle detected: {field_name}")

        self.resolving.add(field_name)
        try:
            cur = args[0]
            for part in field_name.split("."):
                if not isinstance(cur, Mapping):
                    raise KeyError(part)
                cur = cur[part]
                if cur is null or cur is None:
                    raise KeyError(part)

            return cur, field_name
        finally:
            self.resolving.discard(field_name)

class ConfigView(Mapping):
    def __init__(self, *layers, _root=None):
        if not layers:
            raise ValueError("ConfigView requires at least one layer")

        self._layers = [
            layer if isinstance(layer, (Config, ConfigView)) else Config(layer)
            for layer in layers
        ]
        self._resolving = set()

        # Root for interpolation & strictness
        self._root = _root if _root is not None else self
        self._strict = self._layers[0]._strict

    # (Mapping's own __contains__ and get ask __getitem__ and expect a
    # KeyError for a missing key; this one answers null instead.)

    def __contains__(self, key):
        """Whether a layer has *key* (a Config among its keys, a view in one of its layers)."""
        return any(key in layer for layer in self._layers)

    def get(self, key, default=None):
        return self[key] if key in self else default

    def __getitem__(self, key):
        for layer in self._layers:
            if key in layer:
                value = layer[key]

                # A section: a view of it in each layer that has it as one,
                # in order (a view's section is a view), so what one lacks
                # falls through to the next.
                if isinstance(value, (Config, ConfigView)):
                    nested_layers = []
                    for l in self._layers:
                        if key in l:
                            section = l[key]
                            if isinstance(section, (Config, ConfigView)):
                                nested_layers.append(section)
                    return ConfigView(*nested_layers, _root=self._root)

                result = self._resolve(value)
                return null if result is None else result

        return null

    def __setitem__(self, key, value):
        raise TypeError("ConfigView is read-only")

    def __iter__(self):
        """Iterate over values instead of keys to allow iterating over config objects."""
        seen = set()
        for layer in self._layers:
            for k in dict.keys(layer) if isinstance(layer, Config) else layer.keys():
                if k not in seen:
                    seen.add(k)
                    yield self[k]

    def keys(self):
        """Return an iterator over the keys."""
        seen = set()
        for layer in self._layers:
            for k in dict.keys(layer) if isinstance(layer, Config) else layer.keys():
                if k not in seen:
                    seen.add(k)
                    yield k

    def values(self):
        """Return an iterator over the values (Config objects)."""
        seen = set()
        for layer in self._layers:
            for k in dict.keys(layer) if isinstance(layer, Config) else layer.keys():
                if k not in seen:
                    seen.add(k)
                    yield self[k]

    def items(self):
        """Return an iterator over (key, value) pairs."""
        seen = set()
        for layer in self._layers:
            for k in dict.keys(layer) if isinstance(layer, Config) else layer.keys():
                if k not in seen:
                    seen.add(k)
                    yield (k, self[k])

    def __len__(self):
        seen = set()
        for layer in self._layers:
            for k in dict.keys(layer) if isinstance(layer, Config) else layer.keys():
                seen.add(k)
        return len(seen)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return null

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self[name] = value

    def _resolve(self, value):
        if not isinstance(value, str):
            return value

        value = os.path.expandvars(value)

        formatter = _DotFormatter(
            strict=self._root._strict,
            resolving=self._root._resolving,
            root=self._root,
        )

        try:
            return formatter.format(value, self._root)
        except (KeyError, ValueError, IndexError):
            if self._root._strict:
                return value
            return value

    def __or__(self, other):
        return ConfigView(other, *self._layers)

    def __ior__(self, other):
        raise TypeError("ConfigView is immutable")

configs = {}
_stamps = {}  # path -> (mtime, size) of a file other than the main config when it was read
main_path = None
def _apply_option_defaults(cfg):
  """Walk the config tree and merge option_defaults into each child of options.
  Anywhere we find a mapping with both 'option_defaults' and 'options' keys,
  each option gets the defaults merged under it (option's own values take priority)."""
  if not isinstance(cfg, (Config, dict)):
    return
  # Check if this level has option_defaults + options
  has_defaults = 'option_defaults' in cfg and isinstance(cfg.get('option_defaults', None), (Config, dict, Mapping))
  has_options = 'options' in cfg and isinstance(cfg.get('options', None), (Config, dict, Mapping))
  if has_defaults and has_options:
    defaults = cfg['option_defaults']
    options = cfg['options']
    for key in list(dict.keys(options) if isinstance(options, Config) else options.keys()):
      opt = options[key]
      if isinstance(opt, (Config, dict, Mapping)):
        # Merge defaults under the option (option values take priority)
        for dk in (dict.keys(defaults) if isinstance(defaults, Config) else defaults.keys()):
          if dk not in opt or (isinstance(opt, Config) and super(defaultdict, opt).__getitem__(dk) is None):
            # Key not explicitly set in the option — inherit from defaults
            if isinstance(opt, Config):
              opt[dk] = opt._wrap(defaults[dk])
            else:
              opt[dk] = defaults[dk]
      elif opt is None or (hasattr(opt, '__bool__') and not opt):
        # Option is null/None — replace with a copy of defaults
        if isinstance(options, Config):
          options[key] = Config(defaults, _root=cfg._root if isinstance(cfg, Config) else None)
  # Recurse into children
  items = dict.items(cfg) if isinstance(cfg, Config) else cfg.items()
  for k, v in items:
    if isinstance(v, (Config, dict, Mapping)):
      _apply_option_defaults(v)


def get_config(*dicts, path=None, main=False): # because of this, no module that loads the config can be run on its own. the main BBS is meant to be the only one to be run on its own.
  global main_path
  if main and path:
    main_path = path
  if not path:
    path = main_path
  # The main config is read once. Any other file (a user's settings) is
  # read again when it has changed: the Settings page writes it, and fills
  # its form from it, so what it shows must be what is on disk.
  stamp = None
  if path != main_path:
    st = os.stat(path)
    stamp = (st.st_mtime_ns, st.st_size)
  if path not in configs or _stamps.get(path) != stamp:
    with open(path, "r", encoding="utf-8") as f:  # not the locale's code page (cp1252 here)
      cfg = Config(yaml.safe_load(f.read()))
    _apply_option_defaults(cfg)
    configs[path] = cfg
    _stamps[path] = stamp
  return ConfigView(*dicts, configs[path])
