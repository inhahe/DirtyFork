# todo: should we make a custom object that can act like an empty list when the program demands it and return that when the attribute or key isn't found? is that even possible? i think so.
# no, it won't work, because you can't subclass None so the object wouldn't work right with "is None" and "is not None" checks.
# todo: make __getattribute__ get from its dictionary directly on the fly rather than setting all the attributes ahead of time? this is better in case the dictionary changes for some reason.
# todo: update the dictionary on __setattribute__?
# todo: we can override the dictionary get methods to process our dictionaries in the previously returned copy of this program
# todo: detect infinite recursion and stop recursing at some point. i guess the only way is to inspect the stack.
# with all these methods we had to override, maybe it would have just been better to reload the whole dictionary and the new ones and recursively process each value!
# todo: make all dictionary retrieval methods also check for the given attributes, and make all attribute retrieval methods also check for their existence in the dictionary.
# OR it would be easier to make all attribute setting commansd also set the dictionary and vice versa. done that.
# todo: if user does clear(), delete all the attributes too? 
# problem: the class processes values on the way out, but it also processes them on the way in, if they don't start as dictionaries, via Config(dictionary).  
# so that means that format_map is done exactly two levels deep, which is kind of arbitrary.
# oh wait, no, i don't think Config(dictionary) formats anything, it's only on the way out that things are formatted.
# problem: how do i get rid of the infinite loop of updating the attribute updating the dictionary which updates the attribute etc?
# solution: i'm just going to have an internal dictionary and not use the dictionary superclass to store anything. I wonder if I'd ever need the dictionary superclass. 
# i could store everything only in the dict, or everything only in attributes. i chose the attributes so that we don't miss out with dictionary keys that can't be put into attributes.
# but this may raise an exception at some point. but it shouldn't, really, given that it's a config file. 
# oh, wait, what about 
# options:
#   Trade Wars 2002:
#     type: door
# Config saves that, and Trade Wars 2002 can't go into an attribute... hhmm i wonder why i haven't gotten a problem with it, though!
# i guess i'll just use the dictionary methods when i need to access somethin that has spaces.
# that means i'll store everything in the dict, not in attributes, i think it's much easier.
# oh, wait, i do have to process all the keys, don't i!
# items:
#   a:
#     b:
# in that case, a should both be a key and a value..
# but who would store a processing code in something like that?? i don't know, they might.
# todo: process keys recursively when they're retrieved, but only recurse when {} is still present? or don't, because .format_map automatically recurses?
# todo: i think config.foo.bar wouldn't work if config.foo doesn't exist, because config.foo would return None
#       we need to return something else for config.foo if foo doesn't exist, and it needs to be evaluate to false-like if checked
from collections import defaultdict
from collections.abc import Iterable
from yaml import CLoader, load

class Config(defaultdict): 
  def __init__(self, d=None):
    self.d = d
    super().__init__(lambda: None)
    self.update(d)
    for k in d: # todo: hmm, i think this is wrong. i don't think it's converting attributes to dictionary entries. 
      if type(d[k]) is dict:
        setattr(self, self.process(k), Config(d[k])) 
      else:
        setattr(self, self.process(self, k), self.process(self, d[k]))
  def __setattr__(self, attr, value):
    super().__setitem__(attr, value)
  def __delattr__(self, attr):
    super().__delattr__(attr)
    self.__delitem__(self, attr)
  def process(self, value):
    if hasattr(value, "format_map"):
      return value.format_map(self)
    elif isinstance(value, bytes):
      return value.decode("utf-8", errors="ignore").format_map(self.d)
    elif isinstance(value, Iterable) and not isinstance(attr, str):
      for v2 in value:
        yield self.process(self, v2)
  def __getattribute__(self, attr):
    return self.process(attr)
  def transform(self, *dictionaries): # use it like config2 = transform(self, user, global_data, r) # config is already included, so you don't need to pass that.
    d = self                      
    for dictionary in dictionaries:
      d.update(Config(dictionary))
    return d
  def __getitem__(self, key):
    return self.process(self, super().__getitem__(key))
  def get(self, key, default=None):
    return self.process(self, super().get(self.process(self, key), default))
  def __contains__(self, key): 
    return super().__contains__(self.process(key))
  def __iter__(self):
    for key in super().__iter__():
      yield self.process(self, key)  
  def values(self):
    for value in super().__iter__():
      yield self.process(self, value) 
  def items(self):
    for k, v in super().items():
      yield (self.process(self, k), self.process(self, v))
    
def get_config(config_path):
  d = load(open(config_path, "r").read(), Loader=CLoader)
  return Config(d)
