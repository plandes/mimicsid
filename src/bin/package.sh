#!/bin/bash
# @meta {desc: 'model training and packaging', date: '2024-04-06'}

PROG=$(basename $0)
USAGE="usage: $PROG <python home>"
BIN=./dist
CONF_DIR=config
STAGE_DIR=stage
#MODELS="fasttext glove300"
MODELS="glove300"

# don't allow config leak
export MIMICRC=
export MIMICSIDRC=

function log() {
    echo "$PROG: $1"
}

function fail() {
    log $1
    exit 1
}

# sanity check
function check_data() {
    if [ ! -d data ] ; then
	echo "first run src/sh/preprocess.sh from the project root directory, then this again"
	exit 1
    fi
}

# train section and header models
function train() {
    for model in $MODELS ; do
	log "training section model ${model}..."
	$BIN trainprod -c ${CONF_DIR}/${model}.conf
	if [ $? -ne 0 ] ; then
	    fail "model training failed"
	fi

	log "training header model ${model}..."
	$BIN trainprod -c ${CONF_DIR}/${model}.conf \
	     --override msidd_default.model_type=header
	if [ $? -ne 0 ] ; then
	    fail "model training failed"
	fi
    done
}

# package models
function package() {
    mkdir -p $STAGE_DIR
    for model in $MODELS ; do
	log "pacakging section model ${model}..."
	$BIN pack -c ${CONF_DIR}/${model}.conf --modeldir $STAGE_DIR

	log "pacakging section model ${model}..."
	$BIN pack -c ${CONF_DIR}/${model}.conf --modeldir $STAGE_DIR \
	     --override msidd_default.model_type=header
    done
    cp ${HOME}/.cache/zensols/mimicsid/section-id-annotations.zip ${STAGE_DIR}
}

# do all
function main() {
    check_data
    train
    #package
}

main
