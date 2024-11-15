#!/bin/bash

source venv/bin/activate

export TILED_API_KEY=e9fa22c35c4b7414e59d96c265ab46fabdfdea9046c78a88b5f390cea29f6b15

ipython --profile=collection --ipython-dir=$(pwd)/..
