from config import get_config

config = get_config()

# i really want a better place to list the modules, because they need to be loaded when the bbs starts up. but i don't see a better way without being redundant.
modules = {} # todo: would be better if we could do all this with one list comprehension somehow

for module in [destination for destination in config.destinations if destination.type == "module"]:
  modules[module] = import_module(module)
