#!/bin/bash
#@meta {desc: "build production models from scratch", date: "2024-04-11"}

# before starting, make sure to increment: 
#   - resources/default.conf msid_model:version
#   - dist-resources/app.conf deeplearn_model_packer:version

./src/bin/preprocess.sh && \
    cp config/system.conf config/system-sensitive-data.conf && \
    cat /dev/null > config/system.conf && \
    ./src/bin/package.sh > package.log && \
    mv config/system-sensitive-data.conf config/system.conf && \
    mv package.log stage
