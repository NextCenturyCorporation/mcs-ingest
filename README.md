# mcs-ingest
Ingest data into Elasticsearch for MCS

# Setup

## Using python virtual environment:

```bash
python3 -m venv --prompt mcs-ingest venv
. venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
# The following line is the only one unique to Ingest
python -m pip install pymongo
```

## Without virtual environment

```bash
python -m pip install pymongo
```

# Notes to move around:

When creating scenes, you ingest the debug files (move them to their own directory)
Temporarily, don't use an eval with '2' in it
Give the eval and name that doesn't match an evail and easy to find
Use same eval name for scenes and ingest
to get history, need to run (with inputs)
make sure info.team is set in history json (normally set in config when running eval)

commands I used:

python mcs_scene_ingest.py --folder ../genScenes/  --eval_name eval-kd-test --type scene
python mcs_scene_ingest.py --folder ../mcs-devel/SCENE_HISTORY/  --eval_name eval-kd-test --type history    --performer "baseline"


# Example of ingesting a history file
python3 mcs_scene_ingest.py --folder ../generated_scenes/eval2/SCENE_HISTORY_OPICS/ --eval_name eval2_history --performer "OPICS (OSU, UU, NYU)" --type history --scene_folder ../generated_scenes/eval2/physics-scenes/

# Example of ingesting a scene file
python3 mcs_scene_ingest.py --folder ../generated_scenes/intphys_scenes/ --eval_name eval2_intphys_training --type scene

# Unit tests
To run the unit tests, run the command:  python3 -m unittest
