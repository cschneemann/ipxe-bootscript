#!/usr/bin/env python3
import yaml
import cgi
#import cgitb;cgitb.enable()

configfile = "./bootconfig.yaml"

def translate(s):
    s = s.replace("%3A;", ":")
    return s

def get_bootparam(obj, conf_type):
    if obj in config and conf_type in config[obj]:
        return config[obj][conf_type]

    for key in config:
        if obj.startswith(key) and conf_type in config[key]:
            return config[key][conf_type]

    return config["default"][conf_type]

with open(configfile, 'r') as yamlobjects:
    config = yaml.load(yamlobjects, Loader=yaml.FullLoader)

arguments = cgi.FieldStorage()
if "boot" not in arguments:
  BOOT = "default"
else:
  BOOT = translate(arguments["boot"].value).lower()

kernel = get_bootparam(BOOT, "kernel")
initrd = get_bootparam(BOOT, "initrd")
parameter = get_bootparam(BOOT, "parameter")
initrd_name = initrd.split('/')[-1]

print("Content-type: text/plain\n")
print("#!ipxe\n");
print("#booting option {0:s}\n".format(BOOT));
print("kernel {0:s} initrd={1:s} {2:s}".format(kernel, initrd_name, parameter));
print("initrd {0:s}".format(initrd));
print("boot\n");

