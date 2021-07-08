# mcs-ingest

Ingest data into MongoDB for MCS

# Mongo Setup

## Standalone

See the official MongoDB installation page here: https://docs.mongodb.com/manual/installation/

Change each instantiation of the MongoClient in our Python code to: `MongoClient('mongodb://localhost:27017/mcs')`

## With the MCS UI

See the mcs-ui README here: https://github.com/NextCenturyCorporation/mcs-ui/blob/master/README.md

# Python Setup

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

* When creating scenes, ingest the debug files (move them to their own directory)
* When testing, use an eval name that is unique, doesn't look like a real eval, and is easy to notice.
* Make sure you use same eval name for scenes and history when ingesting
* Verify info.team is set in history json (normally set in config when running eval)
* Create files with a metadata level of oracle unless you have a reason to do otherwise

# Unit tests
To run the unit tests, run the command:  python3 -m unittest


# Running deployment scripts
* Update the db_version in deployment_script.py to new db version
* In deployment_script.py call your module and function to update database
* If the db version is not new, no script will be run

## Acknowledgements

This material is based upon work supported by the Defense Advanced Research Projects Agency (DARPA) and Naval Information Warfare Center, Pacific (NIWC Pacific) under Contract No. N6600119C4030. Any opinions, findings and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the DARPA or NIWC Pacific.
