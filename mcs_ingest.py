import io
import json
import os
import re

from pymongo import MongoClient

SCENE_MAPPING_INDEX = "scenes_mapping"
HISTORY_MAPPING_INDEX = "history_mapping"

def copy_indexes(db_string: str,
        client: MongoClient,
        new_collection_name: str,
        mapping_index) -> None:
    mongoDB = client[db_string]

    # Look in mapping collection for last item added
    # Then using the collection tag pull up the collection that is the last eval
    # Using sort -1, will get newest item by _id, using 1 would be oldest
    mapping_collection = mongoDB[mapping_index]
    eval_mapping = mapping_collection.find({}, sort=[('_id', -1)])
    found_mappings = list(eval_mapping)
    if len(found_mappings) > 1:
        old_collection = mongoDB[found_mappings[1]["collection"]]
    else:
        return

    # Get the collection for the current eval using new name
    # Copy the indexes one by one to new collection from last eval
    new_collection = mongoDB[new_collection_name]
    indexes_to_copy = old_collection.index_information()
    for key in indexes_to_copy:
        index_tuple = indexes_to_copy[key]["key"][0]
        new_collection.create_index([(index_tuple[0], int(index_tuple[1]))])


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


def load_json_file(folder: str, file_name: str) -> dict:
    """Read in a json file and decode into a dict.  Can
    be used for history, scene, or other json files."""
    with io.open(
            os.path.join(
                folder, file_name),
            mode='r',
            encoding='utf-8-sig') as json_file:
        return json.loads(json_file.read())
