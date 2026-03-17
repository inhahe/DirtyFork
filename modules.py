from importlib import import_module

from config import get_config

config = get_config()

modules = {}

if config.destinations:
  for name in config.destinations.keys():
    dest = config.destinations[name]
    if dest and dest.type == "module":
      try:
        modules[name] = import_module(name)
      except (ImportError, ModuleNotFoundError):
        pass  # Module not yet implemented
