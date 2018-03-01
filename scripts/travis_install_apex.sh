#!/usr/bin/env bash

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
PARENT_DIR="$( dirname "${REPO_DIR}" )"

#LATEST=$(curl -s https://api.github.com/repos/apex/apex/tags | grep -Eo '"name":.*?[^\\]",'  | head -n 1 | sed 's/[," ]//g' | cut -d ':' -f 2)
#if [ -z $LATEST ]; then
    #LATEST=v0.15.0
#fi
#URL="https://github.com/apex/apex/releases/download/${LATEST}/apex_${LATEST#v}_linux_amd64.tar.gz"

URL="https://github.com/apex/apex/releases/download/v1.0.0-rc2/apex_1.0.0-rc2_linux_amd64.tar.gz"

cd ${PARENT_DIR}
curl -sL ${URL} -o apex.tar.gz
tar -xzf apex.tar.gz
chmod +x apex

echo "Installed apex"
