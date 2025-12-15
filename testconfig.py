import config

i = config.Config({'a': '{b}', 'b': '{c}', 'c': '{a}'}, strict=True)

try:
  print(f"{i.a=}")
except ValueError:
  print("cycle detected") 

try:
  print(f"{i['a']=}")
except ValueError:
  print("cycle detected") 


class A: pass
b = A()
b.c = A()
b.c.d = 1

b.c.e = "{f}"

b.c.f = "{g}"

e = {"f": 2}

b_c = config.Config(b, strict=False)
print(f"{b_c=}")
print(f"{b_c.c.e=}")
print(f"{b_c.c.f=}")
print(f"{b_c.extended(e, deep=False).c.d=}")

h = {}

e_c = config.Config(e)
print(f"{b_c=}")
print(f"{b_c.shallow(e_c)=}")
print(f"{b_c.shallow(e_c).c.d=}")
print(f"{b_c.shallow(h).c.d=}")
print(f"{b_c.shallow(h).c.f=}")
print(f"{b_c.shallow(e_c).c.f=}")

print(f"{(b_c | e_c).c.d=}")

print(f"{(b_c | e_c).c.e=}")

b_c |= e_c
print(f"{b_c.c.d=}")

print(f"{(b_c | e_c)['c']['d']=}")

print(f"{(b_c | e_c)['c']['blah']=}")

print(f"{i.blah=}")  

print(f"{i['blah']=}")  

print(f"{i.foo.bar.baz=}")

x = config.Config({'a': '{b}'}, strict=True)
#print(f"{x.a}=")
y = config.ConfigView(x, {})
print(f"{y.a=}")

