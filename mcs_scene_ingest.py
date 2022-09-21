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

SCENE_MAPPING_INDEX = "scenes_mapping"
SCENE_DEBUG_EXTENSION = "_debug.json"


def copy_indexes(db_string: str,
        client: MongoClient,
        new_collection_name: str) -> None:
    mongoDB = client[db_string]
    print("copy indexes")
    # Look in mapping collection for last item added
    # Then using the collection tag pull up the collection that is the last eval
    # Using sort -1, will get newest item by _id, using 1 would be oldest
    mapping_collection = mongoDB[SCENE_MAPPING_INDEX]
    eval_mapping = mapping_collection.find({}, sort=[('_id', -1)])
    found_mappings = list(eval_mapping)
    if len(found_mappings) > 1:
        old_collection = mongoDB[found_mappings[1]["collection"]]
    else:
        return

    # Get the collection for the current eval using new name
    # Copy the indexes one by one to new collection from last eval
    new_scenes_collection = mongoDB[new_collection_name]
    scene_indexes = old_collection.index_information()
    for key in scene_indexes:
        index_tuple = scene_indexes[key]["key"][0]
        new_scenes_collection.create_index([(index_tuple[0], int(index_tuple[1]))])


def get_scene_collection(
        db_string: str,
        client: MongoClient,
        eval_name: str) -> str:
    mongoDB = client[db_string]
    collection = mongoDB[SCENE_MAPPING_INDEX]
    mapping = collection.find_one(
        {
            "name": eval_name
        }
    )

    if mapping is None:
        eval_number_str = re.sub("[^0-9.]", "", eval_name)
        if "." in eval_number_str:
            eval_number = float(eval_number_str)
        else:
            eval_number = int(eval_number_str)

        collection_name = "eval_" + (str(eval_number)).replace(".", "_") + "_scenes"
        collection.insert_one({"name": eval_name, "collection": collection_name})
        return collection_name
    else:
        return mapping["collection"]


def automated_scene_ingest_file(
        file_name: str,
        folder: str,
        db_string: str,
        client: MongoClient) -> None:
    # Called from mcs_automated_ingest when a new message in pulled
    #    from the AWS Queue, singular scene file
    mongoDB = client[db_string]

    scene_item = build_scene_item(file_name, folder)
    collection_name = get_scene_collection(db_string, client, scene_item["eval"])
    collection = mongoDB[collection_name]
    total_documents = collection.count_documents({})
    if total_documents == 1:
        copy_indexes(db_string, client, collection_name)
    count = collection.count_documents(
        {
            "name": scene_item["name"],
            "eval": scene_item["eval"]
        }
    )

    # Do not insert a scene if we already have it in the database
    #     for this particular evaluation
    if count == 0:
        logging.info(f"Inserting {scene_item['name']}")
        collection.insert_one(scene_item)

    # Add Keys when a new evaluation item is created
    if create_collection_keys.check_collection_has_key(
            scene_item["eval"], mongoDB) is None:
        create_collection_keys.find_collection_keys(
            collection_name, scene_item["eval"], mongoDB)


def build_scene_item(file_name: str, folder: str) -> dict:
    logging.info(f"Ingest scene file: {file_name}")
    scene = load_json_file(folder, file_name)

    scene["eval"] = scene["debug"]["evaluation"]

    eval_number_str = re.sub("[^0-9.]", "", scene["eval"])
    if "." in eval_number_str:
        scene["evalNumber"] = float(eval_number_str)
    else:
        scene["evalNumber"] = int(eval_number_str)

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
