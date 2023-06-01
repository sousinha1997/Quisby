#!/bin/bash

test_pypi_url="https://test.pypi.org/pypi/$2/json"
pypi_url="https://pypi.org/pypi/$2/json"
url=""
if [ "pypi" == $1 ] 
then
url=$pypi_url
else
url=$test_pypi_url
fi

curl $url | jq .info.version | awk -F. -v OFS=. '{$NF += 1 ; print}' | cut -c2- | jinja2 -D package_name=$2 -D version=`awk 'END {print $0}'` setup.j2 > setup.py
