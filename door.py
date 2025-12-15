# config is kinda whack. 
# we need to point to destinations.door, to destination.door.option_defaults, to menu_system.doors.options, to menu_sysem.doors.option_defaults
# but the menu can be changed.. we need a better way to do this.

from platform import processor # why do I have this?
import subprocess, multiprocessing, tempfile, os, shutil
from definitions import *
from common import *
from config import *
config = get_config()
conf = config.destinations.door

class Node:
  def __init__(self, **kwargs):
    for k, v in kwargs.items()
      self.k = v

nodes = {} # each value will be a list of Node instances.  the door name will be the key. the list will be the nodes that are currently in use for that door. 
           # some doors only allow a centain amount of nodes or up to a centain number, so we should delete nodes that are no longer in use and use the next available number

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
  elif len(nodes) == conf.max_nodes:
    r = RetVals()
    r.status="Coud not run door because it would exceed the max number of nodes for the system, which is " + str(DirtyFork.config.doors.max_nodes)
    r.next_destination=r.previous_destination
    return r
  
  node = Node(user=user, r=r)
  nodes[door_config].append(node)
  ns = [d.node_num for d in nodes[door_config]]
  n = 0
  while True:
    if n not in ns:
      break
    n += 1
  node.num_num = n
    
  node.node = len(nodes[door_config]) # todo: make work on Linux and Windows? # 
  # catch: i don't think this works, it could end up with duplicate node.node's
  conf_path = os.path.join(tempfile.gettempdir(), f"dosbox_node{node}.conf")  
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