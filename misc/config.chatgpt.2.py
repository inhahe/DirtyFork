import os
from collections.abc import Mapping, Iterable
from string import Formatter

class _DotFormatter(Formatter):
    """Supports {a.b.c} lookup on dict-like objects."""

    def get_field(self, field_name, args, kwargs):
        value = kwargs
        for part in field_name.split("."):
            value = value[part]
        return value, field_name


class Config(dict):
    def __init__(self, source=None, *, _root=None):
        super().__init__()
        self._root = _root or self

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
        return self._resolve(value)

    def _get(self, key, default=None):
        return self._resolve(super().get(key, default))

    # -----------------------------
    # Internals
    # -----------------------------

    def _wrap(self, value):
        if isinstance(value, Mapping):
            return Config(value, _root=self._root)

        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            return type(value)(self._wrap(v) for v in value)

        return value

    def _resolve(self, value):
        """Resolve strings lazily with env vars and dot-notation."""
        if isinstance(value, str):
            value = os.path.expandvars(value)
            return _DotFormatter().format(value, **self._root)

        if isinstance(value, bytes):
            return os.path.expandvars(
                value.decode("utf-8", errors="ignore")
            )

        return value

    def extended(self, *sources, deep=True):
      """
      Return a copy of this Config, extended with additional sources.

      :param sources: dict-like objects or objects with attributes
      :param deep: if True, merge nested mappings recursively
                    if False, replace values at the top level
      """
      new = Config(_root=None)

      def merge(target, source):
          if isinstance(source, Mapping):
              items = source.items()
          else:
              items = vars(source).items()

          for k, v in items:
              if (
                  deep
                  and k in target
                  and isinstance(target[k], Config)
                  and isinstance(v, Mapping)
              ):
                  merge(target[k], v)
              else:
                  target[k] = target._wrap(v)

      # Merge base config first
      merge(new, self)

      # Merge overlays in order
      for src in sources:
          merge(new, src)

      # Fix root references
      def fix_root(cfg):
          cfg._root = new
          for v in cfg.values():
              if isinstance(v, Config):
                  fix_root(v)

      fix_root(new)
      return new