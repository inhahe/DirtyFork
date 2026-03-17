from definitions import *
from input_output import *

async def run(user, destination, menu_item=None):
  from common import Destinations
  await send(user, cr + lf + "Forums module is not yet implemented." + cr + lf, drain=True)
  return RetVals(status=success, next_destination=Destinations.main, next_menu_item=null)
