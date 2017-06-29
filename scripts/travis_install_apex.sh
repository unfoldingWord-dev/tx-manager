#!/usr/bin/env bash

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
PARENT_DIR="$( dirname "${REPO_DIR}" )"

LATEST=$(curl -s https://api.github.com/repos/apex/apex/tags | grep -Eo '"name":.*?[^\\]",'  | head -n 1 | sed 's/[," ]//g' | cut -d ':' -f 2)
if [ -z $LATEST ]; then
    LATEST=v0.15.0
fi
URL="https://github.com/apex/apex/releases/download/${LATEST}/apex_linux_amd64"
DEST="${PARENT_DIR}/apex"

curl -sL ${URL} -o ${DEST}
chmod +x ${DEST}

echo "Installed apex ${LATEST}"
