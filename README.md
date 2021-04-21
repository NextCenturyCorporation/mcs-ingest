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

# Create files

* See scene generator to create scene files
* In MCS project, use scripts/run_human_input.py or scripts/run_scene_with_command_file.py to create history files
  * history files are normally located in SCENE_HISTORY

# Ingest Sample Commands:

## Ingest scene file
```
python mcs_scene_ingest.py --folder ../genScenes/  --eval_name eval-test --type scene
```

## Ingest history file (requires scenes already ingested)

```
python mcs_scene_ingest.py --folder ../MCS/SCENE_HISTORY/  --eval_name eval-test --type history    --performer "baseline"
```

# Recommendations when testing:

* When creating scenes, you ingest the debug files (move them to their own directory)
* When testing, use an eval name that is unique, doesn't look like a real eval, and is easy to notice.
* Make sure you use same eval name for scenes and history when ingesting
* Verify info.team is set in history json (normally set in config when running eval)

# Unit tests
To run the unit tests, run the command:  python3 -m unittest
