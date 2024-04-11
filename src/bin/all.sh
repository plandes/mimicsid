#!/bin/bash
#@meta {desc: 'build production models from scratch', date: '2024-04-11'}

./src/bin/preprocess.sh && \
    cp config/system.conf config/system-sensitive-data.conf && \
    cat /dev/null > config/system.conf && \
    ./src/bin/package.sh && \
    ./dist summary --validation -o stage/model-performance.csv && \
    mv config/system-sensitive-data.conf config/system.conf
