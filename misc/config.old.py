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

# don't start any yaml keys with '_'

from collections import defaultdict
from collections.abc import Iterable
import yaml
import yaml_include
import pathlib

#yaml.add_constructor("!include", yaml_include.Constructor(base_dir=r'd:\visual studio projects\dirtyfork'))
yaml.add_constructor("!include", yaml_include.Constructor()) # todo: check if !includes actually work with on base_dir provided. if they don't, make it pathlib.abspath(sys.args[0]) or whatever the function is
                                                             # to get the path of the python program.

configs = {}

class Config(defaultdict): 
  def __init__(self, d=None):
    super().__init__(lambda: None)
    if d:
      if isinstance(d, dict):
        self.d = d
        self.update(d)
        for k in d: # todo: hmm, i think this is wrong. i don't think it's converting attributes to dictionary entries. 
          if type(d[k]) is dict:
            setattr(self, self._process(k), Config(d[k])) 
          else:
            setattr(self, self._process(self, k), self._process(self, d[k]))
      else:
        e = {}
        print(self) #debug
        for attr in dir(d):
          if not attr.startswith("_"): 
            print(attr) #debug
            e[attr]=Config(getattr(d, attr))
        return e
  def __setattr__(self, attr, value):
    super().__setitem__(attr, value)
  def __delattr__(self, attr):
    super().__delattr__(attr)
    self.__delitem__(self, attr)
  def _process(self, value):
    if hasattr(value, "format_map"):
      return value.format_map(self)
    elif isinstance(value, bytes):
      return value.decode("utf-8", errors="ignore").format_map(self.d)
    elif isinstance(value, Iterable) and not isinstance(value, str):
      for v2 in value:
        yield self._process(self, v2)
  def __getattribute__(self, attr):
    r = super().__getattribute__(attr)
    if attr.startswith("_"):
      return r
    return self._process(r)
  def transform(self, *dictionaries): # use it like config2 = transform(self, user, global_data, r) # config is already included, so you don't need to pass that.
    d = self                      
    for dictionary in dictionaries:
      d.update(Config(dictionary))
    return d
  def __getitem__(self, key):
    return self._process(self, super().__getitem__(key))
  def get(self, key, default=None):
    return self._process(self, super().get(self._process(self, key), default))
  def __contains__(self, key): 
    return super().__contains__(self._process(key))
  def __iter__(self):
    for key in super().__iter__():
      yield self._process(self, key)  
  def values(self):
    for value in super().__iter__():
      yield self._process(self, value) 
  def items(self):
    for k, v in super().items():
      yield (self._process(self, k), self._process(self, v))
    
def get_config(config_path=None): # todo: we have to pass user_directory at some point and have all future get_configs omit the user_direcotry part.
  if config_path:
    p = pathlib.PurePath(config_path)
    if len(p.parts)==1:
      if not "main" in configs:
        configs["main"] = Config(yaml.load(open(config_path, "r").read(), Loader=yaml.Loader))
      return configs["main"]
  if not config_path in configs:
    configs[config_path] = Config(yaml.load(open(config_path, "r").read(), Loader=yaml.Loader))
  return configs[config_path]
