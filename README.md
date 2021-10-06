# ipxe-bootscript

Simple script that runs on a webserver and returns a default bootconfiguration or a host/group specific one to ipxe Clients.


## Example bootconfig.yaml

```
default:
    kernel: "http://download.opensuse.org/tumbleweed/repo/oss/boot/x86_64/loader/linux"
    initrd: "http://download.opensuse.org/tumbleweed/repo/oss/boot/x86_64/loader/initrd"
    parameter: "splash=silent install=http://download.opensuse.org/tumbleweed/repo/oss/"

# MAC addresses have to be lowercase!
#MAC:
#    kernel: "http://download.opensuse.org/factory/repo/oss/boot/i386/loader/linux"
#    initrd: "http://download.opensuse.org/factory/repo/oss/boot/i386/loader/initrd"
#    parameter: "splash=silent install=http://download.opensuse.org/factory/repo/oss/"

```

## Apache2 configuration

```
Alias /ipxe /opt/ipxe-bootconfig

<Directory /opt/ipxe-bootconfig>
    Options +ExecCGI -Indexes
    DirectoryIndex bootconfig.py
    AddHandler cgi-script .py
    Require all granted
</Directory>
```
