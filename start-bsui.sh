#!/bin/bash

source venv/bin/activate

ipython --profile=collection_tst --ipython-dir=$(pwd)/..
