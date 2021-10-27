#!/bin/bash

# This will generate the data needed for the scorecard integration test
# and then run the integration test.

# Replace this with the location of your MCS
MCS=
MCS=/home/clark/work/mcs/unity/4.6/MCS-AI2-THOR-Unity-App-v0.4.6.x86_64


# For debugging, this will echo all the internal commands
# set -x

# This will give us the full path of directory that the script is in
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Run the following from one up, the main directory for mcs-ingest
cd $SCRIPT_DIR/..

## Make sure that old SCENE_HISTORY files are gone
[[ $(ls -A SCENE_HISTORY 2>/dev/null) ]] && echo "WARNING!!!! SCENE_HISTORY contains old files"


# Generate the data
PYTHONPATH='.' python test_data_generator/scorecard_generate_reopen_data.py $MCS ./tests/golf_0018_15_debug.json
PYTHONPATH='.' python test_data_generator/scorecard_generate_unopenable_data.py $MCS ./tests/golf_0018_15_debug.json
PYTHONPATH='.' python test_data_generator/scorecard_generate_revisit_data.py $MCS ./tests/india_0003_17_debug.json

# Run the integration test
PYTHONPATH='.' python tests/test_scorecard_ground_truth.py
