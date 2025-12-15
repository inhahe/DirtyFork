# problem: I really think door.sys should be up whenever the BBS is. but the system is designed to just import it at the time of executing the menu command.
# solution: all type: module destinations should be loaded when the bbs starts and then just call their run command on demand.
# problem: all those modules are nested deep into the yaml hierarchy, so it's not exactly elegant to collect them all and run them. what else can we do?
# i guess it's fair enough just to make a list somewhere of all module destinations, and then say that the destination.target is pointing to the module in that list.
# can we have a list and use the function to load modules, or do we just have to have a bunch of load commands?
# claude.ai says that's the best way to do it. use the import function. 

from platform import processor
import subprocess, multiprocessing, tempfile, os, shutil
from RetVals import *
from common import *

doors_config = DirtyFork.config.doors

class Node:
  def __init__(self, **kwargs):
    for k, v in kwargs.items()
      self.k = v

nodes = {} # each value will be a list of Node instances. 
for door in doors_config.options: 
  nodes[door] = []   # should i let node.door get out of sync with the place the node is in the list for a give door?

def process(x, user, door_config, r):
  if not isinstance(x, str):
    if type(x) in (float, int):
      return str(x)
    else:
      return x
  d = global_data # warning: don't let users edit your yaml files!
  d.update(config)
  d.update(user.door_config)
  return x.template_map(d)

def create_dosbox_config(node, door_config):
    return f"""
[serial]
serial1=nullmodem server:127.0.0.1 port:{5000+node}

[autoexec]
mount c /doors/temp/node{node}
mount d /doors/{door_config['path']}
c:
d:\\{door_config['command']}
exit
"""

async def run(user, door_config, r): # we could just skip the get_dict step and have a process command in here
  if len(nodes[door_config]) == door_config.max_nodes: 
    r = RetVals()
    r.status="Coud not run door because it would exceed the max number of nodes for the door, which is " + str(door_config.max_nodes))
    r.next_destination=r.previous_destination
    return r
  elif len(nodes) == doors_config.max_nodes:
    r = RetVals()
    r.status="Coud not run door because it would exceed the max number of nodes for the system, which is " + str(DirtyFork.config.doors.max_nodes)
    r.next_destination=r.previous_destination
    return r
  node = Node(user=user, r=r)
  nodes[door_config].append(node)
  node.node = len(nodes[door_config]) # todo: make work on Linux and Windows?
  conf_path = os.path.join(tempfile.gettempdir(), f"dosbox_node{node}.conf")  #it just threw away the tempdir string, so how do i know where to delet it later? (claude.ai helped me with this)
  node_dir = os.path.join(config.doors.base_path,"/temp/node"+node.node)
  os.makedirs(node_dir, exist_ok=True)
  d = {}
  d["node"] = node.node
  d["com"] = 1
  d["baud"] = 115200 # rate doesn't matter anymore, and 115200 is the highest standard rate
  #d["dropfile_path"] = 

  if os.path.isabs(door_config.dir):
    door_dir = os.path.join(doors_config.dir, door_config.dir)
  else:
    door_dir = os.path.abspath(door_config.dir)
  config_path = os.path.join(door_dir, "tmp/dosbox_node_{node}.conf".format_map(d))
  config_content = f"""
[serial]
serial1=nullmodem server:127.0.0.1 port:{5000+node}
[autoexec]
mount c "{node_dir}"
mount d "{door_dir}"
c:
d:\\{door_config['command'].format_map(d)}
exit
"""
  proc = subprocess.Popen(['dosbox', '-conf', config_path])
  node.config_path = config_path
  node.dir = node_dir
  node.process = proc

  with open(conf_path, 'w') as f:
    f.write(config_content)
  subprocess.Popen(['dosbox', '-conf', conf_path, '-noconsole'])
      
  node.process.terminate()
  if os.path.exists(node.config_path)
    os.remove(node.config_path)
    if os.path.exists(node.node_dir):
      shutil.rmtree(node.node_dir)
  nodes[door].remove(node)