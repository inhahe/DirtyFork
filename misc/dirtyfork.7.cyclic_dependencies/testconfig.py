import config
class A: pass
b = A()
b.c = 1
print(config.Config(b))