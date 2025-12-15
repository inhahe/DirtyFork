import os, pathlib
from collections import defaultdict
from collections.abc import Mapping, Iterable
from string import Formatter

import yaml, yaml_include

yaml.add_constructor("!include", yaml_include.Constructor(base_dir=None))
                                                            
class Config(defaultdict):
    def __init__(self, source=None, *, _root=None, strict=True):
        super().__init__(lambda: None) 
        self._root = _root or self

        if _root is None:
          self._strict = strict
          self._resolving = set()  
        else:
          self._strict = _root._strict

        self._sealed = False

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

    def __getattr__(self, name):
        return self._get(name)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self[name] = self._wrap(value)

    def __delattr__(self, name):
        del self[name]

    # -----------------------------
    # Lazy resolution
    # -----------------------------

    def __getitem__(self, key):
        value = super().__getitem__(key)
        if getattr(self._root, '_resolving', None) is None:
            self._root._resolving = set()
        self._root._resolving.add(key)
        try:
            return self._resolve(value)
        finally:
            self._root._resolving.discard(key)

    def _get(self, key, default=None):
        value = super().get(key, default)
        if value is None:
            return value
        if getattr(self._root, '_resolving', None) is None:
            self._root._resolving = set()
        self._root._resolving.add(key)
        try:
            return self._resolve(value)
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
            return type(value)(self._wrap(v) for v in value)

        return value  
      
    def _resolve(self, value):
      if isinstance(value, str):
          value = os.path.expandvars(value)

          formatter = _DotFormatter(
              strict=self._root._strict,
              resolving=self._root._resolving,
              root=self._root,  # Pass the actual Config
          )

          try:
              return formatter.format(value, self._root)
          except KeyError:
              if self._root._strict:
                  raise
              return value

      if isinstance(value, bytes):
          return os.path.expandvars(
              value.decode("utf-8", errors="ignore")
          )

      return value
    
    def seal(self):
        self._sealed = True
        for v in self.values():
            if isinstance(v, Config):
                v.seal()
        return self

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
        self.resolving = resolving or set()
        self.root = root or {}

    def get_field(self, field_name, args, kwargs):
        if field_name in self.resolving:
            raise ValueError(f"Interpolation cycle detected: {field_name}")

        try:
            self.resolving.add(field_name)

            cur = args[0]
            for part in field_name.split("."):
                if not isinstance(cur, Mapping):
                    raise KeyError(part)
                if part not in cur:
                    raise KeyError(part)
                cur = dict.get(cur, part)   # <-- bypass defaultdict

            return cur, field_name

        finally:
            self.resolving.discard(field_name)

class _MergeDirective:
    __slots__ = ("source", "deep")

    def __init__(self, source, *, deep):
        self.source = source
        self.deep = deep

def shallow(source):
    return _MergeDirective(source, deep=False)

def deep(source):
    return _MergeDirective(source, deep=True)

class ConfigView(Mapping):
    def __init__(self, *layers, write_to=None, _root=None):
        if not layers:
            raise ValueError("ConfigView requires at least one layer")

        self._layers = [
            layer if isinstance(layer, (Config, ConfigView)) else Config(layer)
            for layer in layers
        ]

        # Root for interpolation & strictness
        self._root = _root or self
        self._strict = self._layers[0]._strict

        self._write_to = write_to

    def __getitem__(self, key):
        for layer in self._layers:
            if key in layer:
                value = layer[key]

                # Nested mapping → return another view
                if isinstance(value, Config):
                    nested_layers = []
                    for l in self._layers:
                        if key in l and isinstance(l[key], Config):
                            nested_layers.append(l[key])
                    return ConfigView(*nested_layers, _root=self._root)

                return self._resolve(value, resolving={key})

        raise KeyError(key)

    def __setitem__(self, key, value):
        if self._write_to is None:
            raise TypeError("ConfigView is read-only")

        # Ensure nested structure exists in write layer
        if isinstance(value, Mapping):
            value = Config(value)

        if getattr(self, "_sealed", False):
            raise TypeError("Config is sealed")

        self._write_to[key] = value

    def __iter__(self):
        seen = set()
        for layer in self._layers:
            for k in layer:
                if k not in seen:
                    seen.add(k)
                    yield k

    def __len__(self):
        return len(set().union(*self._layers))

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self[name] = value

    def _resolve(self, value, *, resolving):
        if isinstance(value, str):
            value = os.path.expandvars(value)
            formatter = _DotFormatter(
                strict=self._strict,
                resolving=resolving,
            )
            try:
                return formatter.format(value, self)
            except KeyError:
                if self._strict:
                    raise
                return value
        return value

    def freeze(self):
        def materialize(obj):
            if isinstance(obj, ConfigView):
                return Config(
                    {k: materialize(obj[k]) for k in obj},
                    strict=self._strict,
                )
            return obj

        return materialize(self)
    
    def source(self, path):
        parts = self._normalize_path(path)
        results = []

        for layer in self._layers:
            cur = layer
            for p in parts:
                if isinstance(cur, Mapping) and p in cur:
                    cur = cur[p]
                else:
                    cur = None
                    break
            results.append((layer, cur))

        return results

    def __or__(self, other):
        return ConfigView(other, *self._layers)

    def __ior__(self, other):
        raise TypeError("ConfigView is immutable")

configs = {}
main_path = None
def get_config(*dicts, config_path=None, main=False): # because of this, no module that loads the config can be run on its own. the main BBS is meant to be the only one to be run on its own.
  global main_path
  if main and config_path: 
    main_path = config_path    
  if not config_path:
    config_path = main_path
  if not config_path in configs:
      # configs[config_path] = Config(yaml.safe_load(open(config_path, "r").read()))
      # safe_load is better, but i don't know how to make yaml.add_constructor work with it. 
    configs[config_path] = Config(yaml.load(open(config_path, "r").read(), Loader=yaml.Loader))
  return ConfigView(*dicts, configs[config_path])
