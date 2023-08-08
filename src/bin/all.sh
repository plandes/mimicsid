#!/bin/sh


echo "preprossing..." && \
    ./src/bin/preprocess.sh && \
    echo "packaging..." && \
    ./src/bin/package.sh && \
    echo "calculating shas" && \
    ( cd dist ; sha256sum * > sha256sum.txt )
