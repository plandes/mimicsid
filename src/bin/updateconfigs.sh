#!/bin/bash
#@meta {desc: "update model configs", date: "2024-04-12"}
#@meta {doc: "update configurations in already trained models"}

PROG=$(basename $0)
BIN=./dist
CONF_DIR=config
MODELS="fasttext glove300"

export MIMICRC=
export MIMICSIDRC=

function fail() {
    log $1
    exit 1
}

function log() {
    echo "$PROG: $1"
}

# update configurations in already trained models
function updateconfig() {
    for model in $MODELS ; do
	log "updating section model ${model}..."
	$BIN updateconfig -c ${CONF_DIR}/${model}.conf
	if [ $? -ne 0 ] ; then
	    fail "model update failed"
	fi

	log "updating header model ${model}..."
	$BIN updateconfig -c ${CONF_DIR}/${model}.conf \
	     --override msidd_default.model_type=header
	if [ $? -ne 0 ] ; then
	    fail "model training failed"
	fi
    done
}

updateconfig
