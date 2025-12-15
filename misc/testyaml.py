import yaml
import yaml_include

yaml.add_constructor("!include", yaml_include.Constructor())

conf = yaml.load(open("DirtyFork.yaml", "r").read(), Loader=yaml.Loader)

print(conf["user_defaults"])
print(conf["user_defaults"]["scroll_region"])
print(conf["user_defaults"]["keys"])
