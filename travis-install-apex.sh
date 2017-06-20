#!/usr/bin/env bash

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$( dirname "${THIS_DIR}" )"

LATEST=$(curl -s https://api.github.com/repos/apex/apex/tags | grep -Eo '"name":.*?[^\\]",'  | head -n 1 | sed 's/[," ]//g' | cut -d ':' -f 2)
if [ -z $LATEST ]; then
    LATEST=v0.14.0
fi
URL="https://github.com/apex/apex/releases/download/${LATEST}/apex_linux_amd64"
DEST="${PARENT_DIR}/apex"

curl -sL ${URL} -o ${DEST}
chmod +x ${DEST}

echo THIS_DIR=$THIS_DIR
echo PARENT_DIR=$PARENT_DIR
echo LATEST=$LATEST
echo URL=$URL
echo DEST=$DEST
ls -l ${DEST}
