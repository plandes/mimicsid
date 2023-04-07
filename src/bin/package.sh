#!/bin/bash

BIN=./mimicsid

if [ ! -d data ] ; then
    echo "first run src/sh/preprocess.sh from the project root directory, then this again"
    exit 1
fi

# don't allow config leak
export MIMICRC=
export MIMICSIDRC=

for model in fasttext glove300 ; do
    echo "training section model ${model}..."
    $BIN trainprod -c models/${model}.conf

    echo "pacakging section model ${model}..."
    $BIN pack -c models/${model}.conf

    echo "training header model ${model}..."
    $BIN trainprod -c models/${model}.conf --override mimicsid_default.model_type=header

    echo "pacakging section model ${model}..."
    $BIN pack -c models/${model}.conf --override mimicsid_default.model_type=header
done

mkdir -p dist
mv *.zip dist
cp ${HOME}/.cache/zensols/mimicsid/section-id-annotations.zip dist
