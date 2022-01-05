import argparse
import io
import json
import logging
import os
import re
from collections.abc import MutableMapping

from pymongo import MongoClient

import create_collection_keys

# Currently just removing image mag from scene files, might
#    wish to move more keys, or remove so much from the schema
#    that we want to just map the fields we want to the schema
KEYS_TO_DELETE = [
    'image',
    'debug'
]

SCENE_INDEX = "mcs_scenes"

# Convert names used in config to 'pretty' names for UI
TEAM_MAPPING_DICT = {
    "mess": "MESS",
    # Leaving the mit flag for backwards compatibility for now.
    "mit": "IBM-MIT-Harvard-Stanford",
    "cora": "CORA",
    "opics": "OPICS",
    "baseline": "TA2 Baseline"
}

# Convert Eval names used to 'pretty' scene record names for UI
EVAL_SCENE_MAPPING_DICT = {
    "eval_3-5": "Evaluation 3.5 Scenes",
    "eval_3-75": "Evaluation 3.75 Scenes",
    "eval_4": "Evaluation 4 Scenes",
    "eval_5": "Evaluation 5 Scenes",
    "eval_6": "Evaluation 6 Scenes",
    "eval_7": "Evaluation 7 Scenes",
    "eval_8": "Evaluation 8 Scenes",
}

SCENE_DEBUG_EXTENSION = "_debug.json"


def load_json_file(folder: str, file_name: str) -> dict:
    """Read in a json file and decode into a dict.  Can
    be used for history, scene, or other json files."""
    with io.open(
            os.path.join(
                folder, file_name),
            mode='r',
            encoding='utf-8-sig') as json_file:
        return json.loads(json_file.read())


def delete_keys_from_scene(scene, keys) -> dict:
    """Remove keys from a scene object (represented as dict).
    Useful for making the scene smaller (no images) and cleanup"""
    return {
        key: delete_keys_from_scene(value, set(keys))
        if isinstance(value, MutableMapping)
        else value
        for key, value in scene.items()
        if key not in set(keys)
    }


def ingest_to_mongo(index: str, ingest_files: dict, client: MongoClient):
    mongoDB = client['mcs']
    collection = mongoDB[index]
    result = collection.insert_many(ingest_files)
    logging.info(f"Inserted {len(result.inserted_ids)} out of " +
                 f"{len(ingest_files)}. Result: {result}")


def find_scene_files(folder: str) -> dict:
    scene_files = [
        f for f in os.listdir(
            folder) if str(f).endswith(SCENE_DEBUG_EXTENSION)]
    scene_files.sort()
    return scene_files


def build_scene_item(file_name: str, folder: str, eval_name: str) -> dict:
    logging.info(f"Ingest scene file: {file_name}")
    scene = load_json_file(folder, file_name)

    if eval_name is None:
        scene["eval"] = scene["debug"]["evaluation"]
        eval_name = scene["debug"]["evaluation"]
    else:
        scene["eval"] = eval_name

    scene["evalNumber"] = int(re.sub("[^0-9]", "", scene["eval"]))
    scene["scene_num"] = scene["debug"]["sceneNumber"]
    if "sequenceNumber" in scene["debug"]:
        scene["test_num"] = scene["debug"]["sequenceNumber"]
    else:
        scene["test_num"] = scene["debug"]["hypercubeNumber"]

    if "sequenceId" in scene["goal"]["sceneInfo"]:
        scene["goal"]["sceneInfo"]["hypercubeId"] = scene["goal"][
            "sceneInfo"]["sequenceId"]
        del scene["goal"]["sceneInfo"]["sequenceId"]

    scene = delete_keys_from_scene(scene, KEYS_TO_DELETE)

    return scene


def automated_scene_ingest_file(
        file_name: str,
        folder: str,
        db_string: str) -> None:
    # Called from mcs_automated_ingest when a new message in pulled
    #    from the AWS Queue, singular scene file
    # We might want to move mongo user/pass to new file
    client = MongoClient(
        'mongodb://mongomcs:mongomcspassword@localhost:27017/' + db_string)
    mongoDB = client[db_string]

    scene_item = build_scene_item(file_name, folder, None)
    collection = mongoDB[SCENE_INDEX]
    check_exists = collection.find(
        {
            "name": scene_item["name"],
            "evaluation": scene_item["eval"]
        }
    )

    # Do not insert a scene if we already have it in the database
    #     for this particular evaluation
    if check_exists.count() == 0:
        logging.info(f"Inserting {scene_item['name']}")
        collection.insert_one(scene_item)

    # Add Keys when a new evaluation item is created
    if create_collection_keys.check_collection_has_key(
            scene_item["eval"], mongoDB) is None:
        create_collection_keys.find_collection_keys(
            SCENE_INDEX, scene_item["eval"], mongoDB)


def ingest_scene_files(folder: str, eval_name: str) -> None:
    # Legacy way of adding scene files from a folder, leaving code
    #   in case automated ingestion has issues in future, bulk ingest
    scene_files = find_scene_files(folder)
    ingest_scenes = []

    for file in scene_files:
        scene = build_scene_item(file, folder, eval_name)
        ingest_scenes.append(scene)
    # We might want to move mongo user/pass to new file
    client = MongoClient(
        'mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
    mongoDB = client['mcs']

    ingest_to_mongo(SCENE_INDEX, ingest_scenes, client)

    create_collection_keys.find_collection_keys(
        SCENE_INDEX, eval_name, mongoDB)


def determine_evaluation_scene_name(history_eval_name: str) -> str:
    if history_eval_name in EVAL_SCENE_MAPPING_DICT:
        return EVAL_SCENE_MAPPING_DICT[history_eval_name]
    else:
        return history_eval_name


def determine_team_mapping_name(info_team: str) -> str:
    if info_team in TEAM_MAPPING_DICT:
        return TEAM_MAPPING_DICT[info_team]
    else:
        # Add code to convert something like mess2 to MESS2
        return info_team.upper()


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Ingest MCS Scene JSON files into Elasticsearch')
    parser.add_argument(
        '--folder',
        required=True,
        help='Folder location of files to important')
    parser.add_argument(
        '--eval_name',
        required=True,
        help='Name for this eval')
    parser.add_argument(
        '--performer',
        required=False,
        help='Associate this ingest with a performer')
    parser.add_argument(
        '--scene_folder',
        required=False,
        help='Path to folder to link scene history with scene')


    args = parser.parse_args()
    ingest_scene_files(args.folder, args.eval_name)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()
