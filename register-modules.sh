#!/usr/bin/env bash

API_URL=$1

#register md2html
curl --header "Content-Type: application/json" -X POST --data @functions/convert_md2html/module.json "${API_URL}/tx/module"

#register usfm2html
curl --header "Content-Type: application/json" -X POST --data @functions/convert_usfm2html/module.json "${API_URL}/tx/module"

