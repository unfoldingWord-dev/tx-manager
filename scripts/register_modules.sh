#!/usr/bin/env bash

if [ -z $1 ]; then
  echo "The API base URL was not specified."
  echo "Example Usage: register_module.sh https://api.door43.org"
  exit 1;
fi

API_URL=$1

cd "$( dirname "${BASH_SOURCE[0]}" )/.."

#register md2html
curl --header "Content-Type: application/json" -X POST --data @functions/convert_md2html/module.json "${API_URL}/tx/module"

#register usfm2html
curl --header "Content-Type: application/json" -X POST --data @functions/convert_usfm2html/module.json "${API_URL}/tx/module"

