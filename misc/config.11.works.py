import os, pathlib
from collections import defaultdict
from collections.abc import Mapping, Iterable
from string import Formatter
import yaml, yaml_include

#yaml.add_constructor("!include", yaml_include.Constructor(base_dir=r'd:\visual studio projects\dirtyfork'))
yaml.add_constructor("!include", yaml_include.Constructor())
                                                            
class Config(defaultdict):
    def __init__(self, source=None, *, _root=None, strict=True):
        super().__init__(lambda: None) 
        self._root = _root or self

        if _root is None:
          self._strict = strict
          self._resolving = set()  # Add this line
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

    # -----------------------------
    # Attribute access
    # -----------------------------

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
    # -----------------------------
    # Internals
    # -----------------------------

    def _wrap(self, value):
        if isinstance(value, Config):
            return value

        if isinstance(value, Mapping):
            return Config(value, _root=self._root)

        if hasattr(value, "__dict__"):
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
              return formatter.format(value)  # No **self._root
          except KeyError:
              if self._root._strict:
                  raise
              return value

      if isinstance(value, bytes):
          return os.path.expandvars(
              value.decode("utf-8", errors="ignore")
          )

      return value
    # -----------------------------
    # Merge logic
    # -----------------------------

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

    def __or__(self, other):
        return self.extended(other, deep=True)

    def __ior__(self, other):
        if isinstance(other, _MergeDirective):
            return self.merge(other.source, deep=other.deep)
        return self.merge(other, deep=True)

    # -----------------------------
    # Convenience
    # -----------------------------

    def shallow(self, *sources):
        return self.extended(*sources, deep=False)


class _DotFormatter(Formatter):
    def __init__(self, *, strict=True, resolving=None, root=None):
        self.strict = strict
        self.resolving = resolving or set()
        self.root = root or {}

    def get_field(self, field_name, args, kwargs):
        if field_name in self.resolving:
            if self.strict:
                raise ValueError(f"Interpolation cycle detected: {field_name}")
            return "{" + field_name + "}", field_name

        try:
            self.resolving.add(field_name)
            value = self.root  # Use the Config, not unpacked kwargs
            for part in field_name.split("."):
                value = value[part]  # Now triggers Config.__getitem__!
            return value, field_name
        except Exception:
            if self.strict:
                raise
            return "{" + field_name + "}", field_name
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

configs = {}

def get_config(config_path=None): # todo: we have to pass user_directory at some point and have all future get_configs omit the user_direcotry part.
  if config_path:
    p = pathlib.PurePath(config_path)
    if len(p.parts)==1:
      if not "main" in configs:
        #configs["main"] = Config(yaml.safe_load(open(config_path, "r").read())) 
        # safe_load is better, but i don't know how to make yaml.add_constructor work with it. 
        configs["main"] = Config(yaml.load(open(config_path, "r").read(), Loader=yaml.Loader))
      return configs["main"]
  if not config_path in configs:
    #configs[config_path] = Config(yaml.safe_load(open(config_path, "r").read()))
    configs[config_path] = Config(yaml.load(open(config_path, "r").read(), Loader=yaml.Loader))
  return configs[config_path]
