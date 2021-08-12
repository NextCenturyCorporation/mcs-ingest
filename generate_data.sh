#!/bin/bash

source venv/bin/activate

UNITY=/home/clark/work/mcs/unity/4.1/MCS-AI2-THOR-Unity-App-v0.4.1.1.x86_64
SCENE=/home/clark/work/mcs/mcs-ingest/scorecard/testdata/india_0003.json

# python generate_revisit_data.py --level1 /home/clark/work/mcs/unity/MCS-AI2-THOR-Unity-App-v0.3.8.x86_64 /home/clark/work/mcs/mcs-ingest/scorecard/testdata/india_0003.json
# python generate_revisit_data.py --level1 /home/clark/work/mcs/unity/4.3/MCS-AI2-THOR-Unity-App-v0.4.3.x86_64 /home/clark/work/mcs/mcs-ingest/scorecard/testdata/india_0003.json
python scorecard/generator/generate_revisit_data.py --level1 $UNITY $SCENE
