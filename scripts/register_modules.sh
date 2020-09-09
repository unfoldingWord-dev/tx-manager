#!/usr/bin/env bash

if [ -z $1 ]; then
  echo "The API base URL was not specified."
  echo "Example Usage: register_module.sh https://api.door43.org"
  exit 1;
fi

API_URL=$1

cd "$( dirname "${BASH_SOURCE[0]}" )/.."

for f in functions/*/module.json; do
    echo "Registering $f"
    curl --header "Content-Type: application/json" -X POST --data @$f "${API_URL}/tx/register"
done
