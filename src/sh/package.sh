#!/bin/sh

BIN=./mimicsid

echo "about to delete previous models, contune? (CTRL-C to quit)"
rm -rf target model data

echo "batching data"
$BIN batch -c etc/batch.conf

for model in fasttext glove300 ; do
    echo "training model ${model}..."
    $BIN trainprod -c models/${model}.conf
    $BIN trainprod -c models/${model}.conf --override mimicsid_default.model_type=header
done

echo "pacakging model..."
$BIN pack -c models/glove300.conf --override mimicsid_default.model_type=header
