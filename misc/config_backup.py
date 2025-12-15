from yaml import CLoader, load
class Dummy(dict): 
  def __init__(self, d):
    self.update(d)
    for k in d:
      if type(d[k]) is dict:
        setattr(self, k, Dummy(d[k]))
      else:
        setattr(self, k, d[k])
def get_config(config_path):
  d = load(open(config_path, "r").read(), Loader=CLoader)
  return Dummy(d)
    