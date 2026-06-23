# ipxe-bootscript

Simple CGI script that runs on a webserver and returns a default boot configuration or a host/group specific one to iPXE clients.

## Requirements

- Python 3
- `pyyaml` (`pip install pyyaml`)
- `flask` (`pip install flask`) — only needed for the admin WebUI

---

## Configuration

Copy the example config and adjust it to your needs:

```bash
cp bootconfig.yaml.example bootconfig.yaml
```

### YAML-based (default)

Boot configurations are read directly from `bootconfig.yaml`:

```yaml
default:
    kernel: "http://download.opensuse.org/tumbleweed/repo/oss/boot/x86_64/loader/linux"
    initrd: "http://download.opensuse.org/tumbleweed/repo/oss/boot/x86_64/loader/initrd"
    parameter: "splash=silent install=http://download.opensuse.org/tumbleweed/repo/oss/"

# MAC addresses must be lowercase!
aa:bb:cc:dd:ee:ff:
    kernel: "http://example.com/boot/linux"
    initrd: "http://example.com/boot/initrd"
    parameter: "splash=silent install=http://example.com/repo/"
```

### SQLite-based

Set a `database` path in `bootconfig.yaml` to read boot configurations from a SQLite database instead:

```yaml
database: "/etc/ipxe/bootconfig.db"
```

The database must have the following table:

```sql
CREATE TABLE bootconfig (
    identifier TEXT PRIMARY KEY,
    kernel     TEXT NOT NULL,
    initrd     TEXT NOT NULL,
    parameter  TEXT NOT NULL
);
```

Use `default` as the identifier for the fallback entry. When `database` is set, all other entries in `bootconfig.yaml` are ignored.

The admin WebUI (see below) can create and manage the database automatically.

#### CLI: database setup and example entries

```bash
# Create database and table
sqlite3 /etc/ipxe/bootconfig.db "
CREATE TABLE IF NOT EXISTS bootconfig (
    identifier TEXT PRIMARY KEY,
    kernel     TEXT NOT NULL,
    initrd     TEXT NOT NULL,
    parameter  TEXT NOT NULL
);"

# Add default fallback entry
sqlite3 /etc/ipxe/bootconfig.db "
INSERT INTO bootconfig VALUES (
    'default',
    'http://download.opensuse.org/tumbleweed/repo/oss/boot/x86_64/loader/linux',
    'http://download.opensuse.org/tumbleweed/repo/oss/boot/x86_64/loader/initrd',
    'splash=silent install=http://download.opensuse.org/tumbleweed/repo/oss/'
);"

# Add entry for a specific host (full MAC address, must be lowercase)
sqlite3 /etc/ipxe/bootconfig.db "
INSERT INTO bootconfig VALUES (
    'aa:bb:cc:dd:ee:ff',
    'http://example.com/boot/linux',
    'http://example.com/boot/initrd',
    'splash=silent install=http://example.com/repo/'
);"

# Add entry for a group of hosts (MAC prefix)
sqlite3 /etc/ipxe/bootconfig.db "
INSERT INTO bootconfig VALUES (
    'aa:bb:cc',
    'http://example.com/boot/linux',
    'http://example.com/boot/initrd',
    'splash=silent install=http://example.com/repo/'
);"

# List all entries
sqlite3 -column -header /etc/ipxe/bootconfig.db "SELECT * FROM bootconfig;"

# Update an entry
sqlite3 /etc/ipxe/bootconfig.db "
UPDATE bootconfig SET parameter='splash=silent' WHERE identifier='aa:bb:cc:dd:ee:ff';"

# Delete an entry
sqlite3 /etc/ipxe/bootconfig.db "DELETE FROM bootconfig WHERE identifier='aa:bb:cc:dd:ee:ff';"
```

#### CLI: migrate existing bootconfig.yaml entries into the database

Add `database:` to your `bootconfig.yaml` first, then run:

```bash
python3 - <<'EOF'
import sqlite3, yaml

with open("bootconfig.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

db_path = config.pop("database", None)
if not db_path:
    raise SystemExit("No 'database' key found in bootconfig.yaml")

conn = sqlite3.connect(db_path)
conn.execute("""
    CREATE TABLE IF NOT EXISTS bootconfig (
        identifier TEXT PRIMARY KEY,
        kernel     TEXT NOT NULL,
        initrd     TEXT NOT NULL,
        parameter  TEXT NOT NULL
    )
""")

for identifier, values in config.items():
    conn.execute(
        "INSERT OR IGNORE INTO bootconfig VALUES (?, ?, ?, ?)",
        (identifier, values["kernel"], values["initrd"], values["parameter"]),
    )
    print(f"Imported: {identifier}")

conn.commit()
conn.close()
EOF
```

Existing database entries are not overwritten (`INSERT OR IGNORE`). Remove that qualifier and use `INSERT OR REPLACE` if you want to force an update.

### Wildcard / prefix matching

Identifiers support prefix matching. An identifier of `aa:bb:cc` matches any client whose MAC address starts with `aa:bb:cc`. The lookup order is:

1. Exact match
2. First prefix match
3. `default`

MAC addresses passed by iPXE must be **lowercase**.

---

## Deployment

### Apache2

```apache
Alias /ipxe /opt/ipxe-bootscript

<Directory /opt/ipxe-bootscript>
    Options +ExecCGI -Indexes
    DirectoryIndex bootconfig.py
    AddHandler cgi-script .py
    Require all granted
</Directory>
```

### Container (Podman / Docker)

The container serves the CGI bootscript on port **8080** and the admin WebUI on port **5000**. No Apache required.

```bash
# Build
podman build -t ipxe-bootscript .

# Run (mount a directory for the SQLite database)
podman run -d \
  -p 8080:8080 \
  -p 5000:5000 \
  -v /srv/ipxe:/data \
  ipxe-bootscript
```

To use a custom `bootconfig.yaml` (e.g. without a database):

```bash
podman run -d \
  -p 8080:8080 \
  -v /srv/ipxe:/data \
  -v /etc/ipxe/bootconfig.yaml:/app/bootconfig.yaml:ro \
  ipxe-bootscript
```

Environment variables:

| Variable           | Default       | Description                                    |
|--------------------|---------------|------------------------------------------------|
| `BOOT_PORT`        | `8080`        | Port for the iPXE CGI endpoint                 |
| `ADMIN_HOST`       | `127.0.0.1`   | Bind address for the admin WebUI               |
| `ADMIN_PORT`       | `5000`        | Port for the admin WebUI                       |
| `ADMIN_SECRET_KEY` | random        | Flask secret key (set for persistent sessions) |

---

## Admin WebUI

When using the SQLite backend, boot entries can be managed through a browser-based admin interface:

```bash
python3 admin.py
# → http://127.0.0.1:5000
```

The WebUI allows creating, editing, and deleting boot config entries. The SQLite table is created automatically on first start if it does not exist yet.

---

## DHCP configuration

### Apache deployment

```dhcp
option client-arch code 93 = unsigned integer 16;
if exists user-class and option user-class = "iPXE" {
      filename "http://<server-ip>/ipxe/bootconfig.py?boot=${net0/mac}";
} else {
      if option client-arch = 00:07 {
         filename "ipxe.efi";
      } else {
         filename "ipxe.pxe";
      }
}
```

### Container deployment

```dhcp
option client-arch code 93 = unsigned integer 16;
if exists user-class and option user-class = "iPXE" {
      filename "http://<server-ip>:8080/cgi-bin/bootconfig.py?boot=${net0/mac}";
} else {
      if option client-arch = 00:07 {
         filename "ipxe.efi";
      } else {
         filename "ipxe.pxe";
      }
}
```

Replace `<server-ip>` with the IP address of your server.
