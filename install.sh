#!/usr/bin/env bash

set -e
set -o pipefail

SCRIPT_DIR="$(readlink -f "$0" | xargs dirname)"

if [ "$(id -u)" -ne "0" ]; then
	sudo "$0"
	exit "$?"
fi

SLIMDNS_PY_URL="https://raw.githubusercontent.com/dhanar10-forks/slimDNS-py3/076c98e53e8218e4c6491eafef9f9545dc8e78d5/slimDNS.py"

TEMP_DIR="$(mktemp -d)"

trap "rm -rf $TEMP_DIR" EXIT

pushd $TEMP_DIR

apt-get update
apt-get install -y python3-pip
pip3 install dnslib

SITE_PACKAGES_PATH="$(python3 -c 'import site; print(site.getsitepackages()[0])')"
wget -c "$SLIMDNS_PY_URL"
cp slimDNS.py "$SITE_PACKAGES_PATH"

install -m 755 "$SCRIPT_DIR/mdns-proxy.py" /usr/local/bin

cp "$SCRIPT_DIR/mdns-proxy.service" /etc/systemd/system
systemctl daemon-reload
systemctl start mdns-proxy

popd

