#!/bin/bash

source venv/bin/activate

export TILED_API_KEY=e9fa22c35c4b7414e59d96c265ab46fabdfdea9046c78a88b5f390cea29f6b15

rm -f -r /tmp/tiled_storage
mkdir /tmp/tiled_storage
tiled catalog init sqlite+aiosqlite:////tmp/tiled_storage/catalog.db

tiled serve catalog \
    /tmp/tiled_storage/catalog.db \
    -w /tmp/tiled_storage/data/ \
    --api-key=$TILED_API_KEY \
    -r /nsls2/data/tst/
