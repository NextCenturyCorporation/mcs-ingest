import json
import os
import re
import sys
import argparse
import mcs_scene_schema
import mcs_scene_history_schema

from mcs_elasticsearch import MCSElasticSearch
from collections.abc import MutableMapping

# Currently just removing image mag from scene files, might wish to move more keys, 
#    or remove so much from the schema that we want to just map the fields we want to the schema
KEYS_TO_DELETE = ['image']

# Elastic Search Schema Constants
SCENE_INDEX = "mcs_scenes"
SCENE_TYPE = "scenes"
HISTORY_INDEX = "mcs_history"
HISTORY_TYPE = "history"


def load_scene_file(folder: str, file_name: str) -> dict:
    with open(os.path.join(folder, file_name)) as json_file:
        return json.load(json_file)


def load_history_file(folder: str, file_name: str) -> dict:
    with open(os.path.join(folder, file_name)) as file:
        data = "[" + file.read().replace('}{', '},{') + "]"
        return json.loads(data) 


def delete_keys_from_scene(scene, keys) -> dict:
    new_scene = {}
    for key, value in scene.items():
        if key not in set(keys):
            if isinstance(value, MutableMapping):
                new_scene[key] = delete_keys_from_scene(value, set(keys))
            else:
                new_scene[key] = value

    return new_scene


def ingest_elastic_search(index: str, eval_name: str, replace_index: bool, schema:dict, ingest_files: dict) -> None:
    elastic_search = MCSElasticSearch(index, eval_name, replace_index, schema)
    elastic_search.bulk_upload(ingest_files)


def find_scene_files(folder: str) -> dict:
    scene_files = [f for f in os.listdir(folder) if str(f).endswith("debug.json")]
    if not scene_files:
        # For ingesting files that we generated before we started generating debug files (i.e. - Interaction Training Data)
        scene_files = [f for f in os.listdir(folder) if str(f).endswith(".json")]
    scene_files.sort()
    return scene_files


def find_history_files(folder: str) -> dict:
    history_files = [f for f in os.listdir(folder) if str(f).endswith(".txt")]
    history_files.sort()
    return history_files


def get_index_dict(index: str, index_type: str) -> dict:
    return {
        "index": {
            "_index": index,
            "_type": index_type
        }
    }


def get_scene_name_from_history_file(file_name: str) -> str:
    # Currently checking for the part of the file name before the data, we could remove this by adding
    #    the scene name into the history file at some point in a future ticket.
    reg = re.compile("-202.+-")
    for match in re.finditer(reg, file_name):
        return file_name[0:match.start()]


def ingest_scene_files(folder: str, eval_name: str, performer: str) -> None:
    scene_files = find_scene_files(folder)
    ingest_scenes = []

    for file in scene_files:
        print("Ingest scene file: {}".format(file))
        scene = load_scene_file(folder, file)
        scene["eval"] = eval_name
        scene["performer"] = performer

        scene = delete_keys_from_scene(scene, KEYS_TO_DELETE)

        ingest_scenes.append(get_index_dict(SCENE_INDEX, SCENE_TYPE))
        ingest_scenes.append(scene)

    ingest_elastic_search(SCENE_INDEX, eval_name, False, mcs_scene_schema.get_scene_schema(), ingest_scenes)


def ingest_history_files(folder: str, eval_name: str, performer: str) -> None:
    history_files = find_history_files(folder)
    ingest_history = []

    for file in history_files:
        print("Ingest history files: {}".format(file))
        history = load_history_file(folder, file)

        history_item = {}
        history_item["eval"] = eval_name
        history_item["performer"] = performer
        history_item["name"] = get_scene_name_from_history_file(file)

        steps = []
        for step in history:
            if "step" in step:
                new_step = {}
                new_step["stepNumber"] = step["step"]
                new_step["action"] = step["action"]
                new_step["args"] = step["args"]
                steps.append(new_step)
            if "classification" in step:
                history_item["score"] = {}
                history_item["score"]["classification"] = step["classification"]
                history_item["score"]["confidence"] = step["confidence"]

        history_item["steps"] = steps

        ingest_history.append(get_index_dict(HISTORY_INDEX, HISTORY_TYPE))
        ingest_history.append(history_item)

    ingest_elastic_search("mcs_history", eval_name, False, mcs_scene_history_schema.get_scene_history_schema(), ingest_history)


def main(argv) -> None:
    parser = argparse.ArgumentParser(description='Ingest MCS Scene JSON files into Elasticsearch')
    parser.add_argument('--folder', required=True, help='Folder location of files to important')
    parser.add_argument('--eval_name', required=True, help='Name for this eval')
    parser.add_argument('--performer', required=False, help='Associate this ingest with a performer')
    parser.add_argument('--type', required=True, help='Choose if ingesting scenes or history', choices=['scene', 'history'])

    args = parser.parse_args(argv[1:])

    if args.type == 'scene':
        ingest_scene_files(args.folder, args.eval_name, args.performer)
    if args.type == 'history':
        ingest_history_files(args.folder, args.eval_name, args.performer)


if __name__ == '__main__':
    main(sys.argv)