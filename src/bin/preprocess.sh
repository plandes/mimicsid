#!/bin/bash

BIN=./mimicsid

# don't allow config leak
export MIMICRC=
export MIMICSIDRC=

echo "about to delete previous models, contune? (CTRL-C to quit)"
read

echo "deleting any old models..."
rm -rf target model data dist

echo "batching data"
$BIN batch -c etc/batch.conf
