#!/bin/bash

BIN=./dist
CONFIG=config/system.conf
FAST=1
# don't allow config leak
export MIMICRC=
export MIMICSIDRC=

function confirm() {
    echo "about to delete previous models, contune? (CTRL-C to quit)"
    read
}

function clean() {
    echo "deleting old build artifacts and models..."
    rm -rf target model data stage
}

function preempt() {
    echo "parsing admissions, notes and docs"
    if [ $FAST -eq 1 ] ; then
	$BIN preempt -c ${CONFIG} -w 1 --maxadm 10
    else
	$BIN preempt -c ${CONFIG} -w 4
    fi
}

function batch() {
    echo "batching data"
    if [ $FAST -eq 1 ] ; then
	$BIN batch -c ${CONFIG} --override \
	     'model_settings.epochs=2,batch_stash.batch_limit=3'
    else
	$BIN batch -c ${CONFIG}
    fi
}

function main() {
    confirm
    clean
    preempt
    batch
}

main
