#!/usr/bin/env python
import yaml
import cgi
#import cgitb;cgitb.enable()

configfile = "./bootconfig.yaml"

def translate(s):
    s = s.replace("%3A;", ":")
    return s

def get_bootparam(obj, conf_type):
    try:
        config[obj][conf_type]
    except KeyError:
        obj = "default"
    return config[obj][conf_type]

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

print("Content-type: text/plain\n")
print("#!ipxe\n");
print("#booting option {0:s}\n".format(BOOT));
print("kernel {0:s} initrd={1:s} {2:s}".format(kernel, initrd, parameter));
print("initrd {0:s}".format(initrd));
print("boot\n");

