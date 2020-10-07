#!/usr/bin/env bash

set -e
set -o pipefail

if [ "$(id -u)" -ne "0" ]; then
	sudo "$0"
	exit "$?"
fi

SLIMDNS_PY_URL="https://raw.githubusercontent.com/dhanar10-forks/slimDNS-py3/076c98e53e8218e4c6491eafef9f9545dc8e78d5/slimDNS.py"
SITE_PACKAGES_PATH="$(python3 -c 'import site; print(site.getsitepackages()[0])')"

TEMP_DIR="$(mktemp -d)"

trap "rm -rf $TEMP_DIR" EXIT

pushd $TEMP_DIR

wget -c "$SLIMDNS_PY_URL"
cp slimDNS.py "$SITE_PACKAGES_PATH"

install -m 755 mdns-proxy.py /usr/local/bin

cp mdns-proxy.service /etc/systemd/system
systemctl daemon-reload
systemctl start mdns-proxy

popd

