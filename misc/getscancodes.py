import pprint
d = {}
o=open("scancodes.txt","r")
for line in o:
  k, v = line.split("=")
  v = v.strip()
  if len(v)%2==1: 
    raise ValueError(v)
  code = b"" 
  for x in range(len(v.strip())//2):
    code += bytes(
                  [int
                   (v
                    [x*2:x*2+2], 16
                   )
                  ]
                 )
  d[code] = k
pprint.pprint(d)