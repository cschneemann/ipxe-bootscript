# ipxe-bootscript

Simple script that runs on a webserver and returns a default bootconfiguration or a host/group specific one to ipxe Clients.


## Example bootconfig.yalm

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

## DHCP configuration

```
option client-arch code 93 = unsigned integer 16;
if exists user-class and option user-class = "iPXE" {
      filename "http://192.168.254.3/ipxe/bootconfig.py?boot=${net0/mac}";
} else {
      if option client-arch = 00:07 {
         filename "ipxe.efi";
      }  else {
         filename "ipxe.pxe";
      }
}
```
