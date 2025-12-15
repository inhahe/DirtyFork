# todo: should we make a custom object that can act like an empty list when the program demands it and return that when the attribute or key isn't found? is that even possible? i think so.
# no, it won't work, because you can't subclass None so the object wouldn't work right with "is None" and "is not None" checks.
# todo: make __getattribute__ get from its dictionary directly on the fly rather than setting all the attributes ahead of time? this is better in case the dictionary changes for some reason.
# todo: update the dictionary on __setattribute__?
from collections import defaultdict
from yaml import CLoader, load
class Dummy(defaultdict): 
  def __init__(self, d):
    super().__init__(lambda: None)
    self.update(d)
    for k in d:
      if type(d[k]) is dict:
        setattr(self, k, Dummy(d[k]))
      else:
        setattr(self, k, d[k])
  def __getattribute__(self, attr):
    try:
      return super().__getattribute__(attr)
    except AttributeError:
      return None
def get_config(config_path):
  d = load(open(config_path, "r").read(), Loader=CLoader)
  return Dummy(d)
    