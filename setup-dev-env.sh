#!/bin/bash


<<<<<<< Updated upstream
declare -a REPOS=("ophyd-async" "bluesky" "event-model" "tiled" "nslsii")
=======
declare -a REPOS=("ophyd-async" "bluesky" "event-model" "tiled" "nslsii", "bluesky-queueserver", "bluesky-widgets", "bluesky-queueserver-api")
>>>>>>> Stashed changes

rm -rf venv overlays

mkdir venv
cd venv
python3.11 -m venv .
source bin/activate
cd ..


mkdir overlays
cd overlays
for repo in "${REPOS[@]}";
do
git clone https://github.com/bluesky/$repo
cd $repo
pip install -e .[dev]
cd ..
done

<<<<<<< Updated upstream
conda deactivate
=======
deactivate
>>>>>>> Stashed changes
