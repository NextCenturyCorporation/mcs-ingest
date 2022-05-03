#!/bin/bash

set -x

source ../../venv/bin/activate

# Make sure the output directoy is clean
rm ./SCENE_HISTORY/gen_*.json || true

# Generate the output data from moving around the ILE
python scorecard_generate_move_toward.py ../test_data/india_0003_17_debug.json
python scorecard_generate_relook.py ../test_data/golf_0018_15_debug.json
python scorecard_generate_repeat_failed.py ../test_data/golf_0018_15_debug.json
python scorecard_generate_revisit_data.py ../test_data/india_0003_17_debug.json
python scorecard_generate_unopenable_data.py ../test_data/golf_0018_15_debug.json
python scorecard_generate_ramp.py ../test_data/ramps_eval_5_ex_1.json

# Replace the data in the test_data directory
rm ../test_data/gen_*.json || true

cd SCENE_HISTORY
for hist_file in `ls gen_*.json`
do
    first_part=`echo $hist_file | cut -d '-' -f 1`
    newname="${first_part}.json"
    cp $hist_file ../../test_data/$newname
done
    
set x
