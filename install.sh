#!/usr/bin/env bash

set -e
set -o pipefail

SITE_PACKAGES_PATH="$(python3 -c 'import site; print(site.getsitepackages()[0])')"
SLIMDNS_PY_URL="https://raw.githubusercontent.com/dhanar10-forks/slimDNS-py3/076c98e53e8218e4c6491eafef9f9545dc8e78d5/slimDNS.py"

wget -c "$SLIMDNS_PY_URL"
cp slimDNS.py "$SITE_PACKAGES_PATH"

cp mdns-proxy.py /usr/local/bin
chmod +x /usr/local/bin/mdns-proxy.py

cp mdns-proxy.service /etc/systemd/system
systemctl daemon-reload
systemctl start mdns-proxy
