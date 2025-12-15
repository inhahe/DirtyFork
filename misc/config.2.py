from yaml import CLoader, load
class Dummy(dict): 
  def __init__(self):

def get_object(d):
  o = Dummy()  
  for k in d:
    if type(d[k]) is dict:
      setattr(o, k, get_object(d[k]))
    else:
      setattr(o, k, d[k])
  return o
def get_config(config_path):
  d = load(open(config_path, "r").read(), Loader=CLoader)
  return d, get_object(d)
    