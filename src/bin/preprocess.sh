#!/bin/bash

BIN=./dist
CONFIG=config/system.conf

# don't allow config leak
export MIMICRC=
export MIMICSIDRC=

echo "about to delete previous models, contune? (CTRL-C to quit)"
read

echo "deleting old build artifacts and models..."
rm -rf target model data stage

echo "parsing admissions, notes and docs"
# TODO: remove maxadms
$BIN preempt -w 4 -c ${CONFIG} --maxadm 10

echo "batching data"
$BIN batch -c ${CONFIG}
