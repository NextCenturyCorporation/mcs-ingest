import logging
import re
from collections.abc import MutableMapping

from pymongo import MongoClient
from mcs_ingest import copy_indexes, load_json_file, get_scene_collection

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
        copy_indexes(db_string, client, collection_name, SCENE_MAPPING_INDEX)
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

    if "path" in scene["debug"]:
        scene["path"] = scene["debug"]["path"]

    if "slowPath" in scene["debug"]:
        scene["slowPath"] = scene["debug"]["slowPath"]

    scene = delete_keys_from_scene(scene, KEYS_TO_DELETE)

    return scene


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
