#!/usr/bin/env bash

set -e
set -o pipefail

if [ "$(id -u)" -ne "0" ]; then
	sudo "$0"
	exit "$?"
fi

MDNS_PROXY_PY_URL="https://raw.githubusercontent.com/dhanar10/mdns-proxy/master/mdns-proxy.py"
MDNS_PROXY_SERVICE_URL="https://raw.githubusercontent.com/dhanar10/mdns-proxy/master/mdns-proxy.service"
SLIMDNS_PY_URL="https://raw.githubusercontent.com/dhanar10-forks/slimDNS-py3/076c98e53e8218e4c6491eafef9f9545dc8e78d5/slimDNS.py"

TEMP_DIR="$(mktemp -d)"

trap "rm -rf $TEMP_DIR" EXIT

cd $TEMP_DIR

wget -c "$MDNS_PROXY_PY_URL"
wget -c "$MDNS_PROXY_SERVICE_URL"
wget -c "$SLIMDNS_PY_URL"

apt-get update
apt-get install -y python3-pip
pip3 install dnslib

SITE_PACKAGES_DIR="$(python3 -c 'import site; print(site.getsitepackages()[0])')"
cp slimDNS.py "$SITE_PACKAGES_DIR"
install -m 755 "mdns-proxy.py" /usr/local/bin
cp "mdns-proxy.service" /etc/systemd/system

systemctl daemon-reload
systemctl start mdns-proxy

cd ..
