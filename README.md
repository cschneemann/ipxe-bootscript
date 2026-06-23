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

## nginx configuration

nginx does not support CGI natively — `fcgiwrap` is required to execute the script:

```bash
# Debian/Ubuntu
apt install fcgiwrap

# openSUSE
zypper install fcgiwrap
systemctl enable --now fcgiwrap.socket
```

```nginx
server {
    listen 80;
    server_name _;

    location = /ipxe/bootconfig.py {
        fastcgi_pass unix:/run/fcgiwrap.socket;
        fastcgi_param SCRIPT_FILENAME /opt/ipxe-bootscript/bootconfig.py;
        include fastcgi_params;
    }
}
```

## Container (Podman / Docker)

```bash
# Build
podman build -t ipxe-bootscript .

# Run
podman run -d \
  -p 8080:8080 \
  -v /etc/ipxe/bootconfig.yaml:/app/bootconfig.yaml:ro \
  ipxe-bootscript
```

The `BOOT_PORT` environment variable controls the listening port (default: `8080`).

## DHCP configuration

### Apache / nginx

```dhcp
option client-arch code 93 = unsigned integer 16;
if exists user-class and option user-class = "iPXE" {
      filename "http://<server-ip>/ipxe/bootconfig.py?boot=${net0/mac}";
} else {
      if option client-arch = 00:07 {
         filename "ipxe.efi";
      }  else {
         filename "ipxe.pxe";
      }
}
```

### Container

```dhcp
option client-arch code 93 = unsigned integer 16;
if exists user-class and option user-class = "iPXE" {
      filename "http://<server-ip>:8080/cgi-bin/bootconfig.py?boot=${net0/mac}";
} else {
      if option client-arch = 00:07 {
         filename "ipxe.efi";
      }  else {
         filename "ipxe.pxe";
      }
}
```

Replace `<server-ip>` with the IP address of your server.
