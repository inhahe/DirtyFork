from collections.abc import Mapping, Iterable

class Config(dict):
    """
    A dictionary that:
      - allows attribute access (cfg.x)
      - recursively wraps nested mappings
      - supports string interpolation via format_map
    """

    def __init__(self, source=None):
        super().__init__()

        if source is None:
            return

        # Dict-like input
        if isinstance(source, Mapping):
            for k, v in source.items():
                self[k] = self._wrap(v)

        # Object input
        else:
            for k, v in vars(source).items():
                self[k] = self._wrap(v)

    # -----------------------------
    # Attribute access
    # -----------------------------

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        self[name] = self._wrap(value)

    def __delattr__(self, name):
        del self[name]

    # -----------------------------
    # Value processing
    # -----------------------------

    def _wrap(self, value):
        """Recursively wrap values into Config where appropriate."""
        if isinstance(value, Mapping):
            return Config(value)

        if isinstance(value, str):
            return value.format_map(self)

        if isinstance(value, bytes):
            return value.decode("utf-8", errors="ignore").format_map(self)

        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            return type(value)(self._wrap(v) for v in value)

        return value