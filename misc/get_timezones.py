import json
d = {}
for line in open("timezones.txt", "r", encoding="utf-8"):
   try:
     fields = line.split()
     timezones = [fields[0]]
     if fields[1].startswith("("):
       timezones += fields[1][1:-1].split("/")
     offset = fields[-1].strip()[-6:]
     if offset[0] == "−":
       sign=-1
     elif offset[0] == "+":
       sign=1
     hour, min = offset[1:].split(":")
     offsethour = int(hour)
     offsetmin = int(min)
     for timezone in timezones:
       d[timezone] = (offsethour*sign, offsetmin*sign)
   except:
     print(line)
json.dump(d, open("time_zones.json", "w"))    
     
  