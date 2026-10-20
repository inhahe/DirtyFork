from importlib import import_module

from config import get_config
from logger import log

config = get_config()

modules = {}

if config.destinations:
  for name in config.destinations.keys():
    dest = config.destinations[name]
    if dest and dest.type == "module":
      try:
        modules[name] = import_module(name)
      except ModuleNotFoundError as e:
        if e.name != name:
          # The module exists but something it imports doesn't (e.g. a missing
          # package): that is a broken install, not an unimplemented module.
          log.error("Module '%s' could not be loaded: %s", name, e)
        # else: module not yet implemented
      except ImportError as e:
        log.error("Module '%s' could not be loaded: %s", name, e)
