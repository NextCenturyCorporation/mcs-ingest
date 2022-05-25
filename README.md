# mcs-ingest

Ingest data into MongoDB for MCS

## Mongo Setup

### Standalone

See the official MongoDB installation page here: https://docs.mongodb.com/manual/installation/

Change each instantiation of the MongoClient in our Python code to: `MongoClient('mongodb://localhost:27017/mcs')`

### With the MCS UI

See the mcs-ui README here: https://github.com/NextCenturyCorporation/mcs-ui/blob/master/README.md

## Python Setup

### Using python virtual environment

```bash
python3 -m venv --prompt mcs-ingest venv
. venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
# The following line is the only one unique to Ingest
python -m pip install -r requirements.txt
```

## Create Files

* See scene generator to create scene files
* In MCS project, use scripts/run_human_input.py or scripts/run_scene_with_command_file.py to create history files
  * history files are normally located in SCENE_HISTORY

## Ingest Sample Commands (for testing locally)

### Ingest scene file
```
python local_scene_ingest.py --folder ../genScenes/
```

### Ingest history file (requires scenes already ingested)

```
python local_history_ingest.py --folder ../MCS/SCENE_HISTORY/
```

## Recommendations When Testing

* When creating scenes, ingest the debug files (move them to their own directory)
* Verify info.evaluation_name and info.team is set in history json (normally set in config when running eval)
* When testing, use an evaluation name that follows the current naming convention so that everything is mapped correctly (i.e. "Evaluation 4 Scenes" in the scene file, "eval_4" in the history file).
* Create files with a metadata level of oracle unless you have a reason to do otherwise

## Unit Tests

To run the unit tests, run the command: `python -m unittest`

### Notes

- Some unit tests will start a MongoDB instance in a docker container, and then stop it once the tests are done. Each time you run the unit tests, python will automatically download the latest `mongo` docker image, if needed.
- If you get a docker permissions or connection refused error, you might need to add yourself to the `docker` group; see the [instructions here](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user). Do NOT use [rootless docker](https://docs.docker.com/engine/security/rootless/) because it uses a different `docker.sock` file than the one we reference in the unit tests.

## Running Deployment Scripts

* Update the db_version in deployment_script.py to new db version
* In deployment_script.py call your module and function to update database
* If the db version is not new, no script will be run

## Scorecard

See [scorecard/README.md](./scorecard/README.md) for details.

## Acknowledgements

This material is based upon work supported by the Defense Advanced Research Projects Agency (DARPA) and Naval Information Warfare Center, Pacific (NIWC Pacific) under Contract No. N6600119C4030. Any opinions, findings and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the DARPA or NIWC Pacific.
