import json
import os
import re
import sys
import argparse
import math
import mcs_scene_schema
import mcs_scene_history_schema
import io

from mcs_elasticsearch import MCSElasticSearch
from collections.abc import MutableMapping 
from pymongo import MongoClient

client = MongoClient('mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
mongoDB = client['mcs']

# Currently just removing image mag from scene files, might wish to move more keys, 
#    or remove so much from the schema that we want to just map the fields we want to the schema
KEYS_TO_DELETE = ['image']

# Elastic Search Schema Constants
SCENE_INDEX = "mcs_scenes"
SCENE_TYPE = "scenes"
HISTORY_INDEX = "mcs_history"
HISTORY_TYPE = "history"

COLOR_LIST = ["black","blue","brown","green","grey","orange","purple","red","white","yellow"]
MATERIAL_LIST = ["ceramic","food","glass","hollow","fabric","metal","organic","paper","plastic","rubber","soap","sponge","stone","wax","wood"]

def load_json_file(folder: str, file_name: str) -> dict:
    with io.open(os.path.join(folder, file_name), mode='r', encoding='utf-8-sig') as json_file:
        return json.loads(json_file.read())


def delete_keys_from_scene(scene, keys) -> dict:
    new_scene = {}
    for key, value in scene.items():
        if key not in set(keys):
            if isinstance(value, MutableMapping):
                new_scene[key] = delete_keys_from_scene(value, set(keys))
            else:
                new_scene[key] = value

    return new_scene


def recursive_find_keys(x, keys, append_string):
    l = list(x.keys())
    for item in l:
        if isinstance(x[item], dict):
            recursive_find_keys(x[item], keys, append_string + item + ".")
        elif isinstance(x[item], list):
            for arrayItem in x[item]:
                if isinstance(arrayItem, dict):
                    recursive_find_keys(arrayItem, keys, append_string + item + ".")        
        elif append_string + item not in keys:
            keys.append(append_string + item)


def ingest_to_mongo(index: str, ingest_files: dict):
    collection = mongoDB[index]
    result = collection.insert_many(ingest_files)
    print(result)

    keys = []
    mydoc = collection.find()
    for x in mydoc:
        recursive_find_keys(x, keys, "")

    keys_dict = {}
    keys_dict["keys"] = keys

    collection = mongoDB[index + "_keys"]
    collection.drop()
    result = collection.insert_one(keys_dict)
    print(result)


def find_scene_files(folder: str) -> dict:
    scene_files = [f for f in os.listdir(folder) if str(f).endswith("debug.json")]
    if not scene_files:
        # For ingesting files that we generated before we started generating debug files (i.e. - Interaction Training Data)
        scene_files = [f for f in os.listdir(folder) if str(f).endswith(".json")]
    scene_files.sort()
    return scene_files


def find_history_files(folder: str) -> dict:
    history_files = [f for f in os.listdir(folder) if str(f).endswith(".json")]
    history_files.sort()
    return history_files


def get_index_dict(index: str, index_type: str) -> dict:
    return {
        "index": {
            "_index": index,
            "_type": index_type
        }
    }


def ingest_scene_files(folder: str, eval_name: str, performer: str) -> None:
    scene_files = find_scene_files(folder)
    ingest_scenes = []

    for file in scene_files:
        print("Ingest scene file: {}".format(file))
        scene = load_json_file(folder, file)
        scene["eval"] = eval_name
        scene["performer"] = performer
        scene["test_type"] = scene["name"][:-7]
        scene["scene_num"] = scene["name"][-6:-2]
        scene["scene_part_num"] = scene["name"][-1:]

        scene = delete_keys_from_scene(scene, KEYS_TO_DELETE)
        ingest_scenes.append(scene)

    ingest_to_mongo(SCENE_INDEX, ingest_scenes)


def ingest_history_files(folder: str, eval_name: str, performer: str, scene_folder: str) -> None:
    history_files = find_history_files(folder)
    ingest_history = []

    for file in history_files:
        print("Ingest history files: {}".format(file))
        history = load_json_file(folder, file)

        history_item = {}
        history_item["eval"] = eval_name
        history_item["performer"] = performer
        history_item["name"] = history["info"]["name"]

        history_item["test_type"] = history_item["name"][:-7]
        history_item["scene_num"] = history_item["name"][-6:-2]
        history_item["scene_part_num"] = history_item["name"][-1:]
        history_item["url_string"] = "test_type=" + history_item["test_type"] + "&scene_num=" + history_item["scene_num"] + "&scene_part_num=" + history_item["scene_part_num"] + "&performer=" + history_item["performer"]

        history_item["flags"] = {}
        history_item["flags"]["remove"] = False
        history_item["flags"]["interest"] = False

        steps = []
        number_steps = 0
        interactive_goal_achieved = 0
        for step in history["steps"]:
            number_steps += 1
            new_step = {}
            new_step["stepNumber"] = step["step"]
            new_step["action"] = step["action"]
            new_step["args"] = step["args"]
            output = {}
            if("output" in step):
                output["return_status"] = step["output"]["return_status"]
                output["reward"] = step["output"]["reward"]
                if(output["reward"] == 1):
                    interactive_goal_achieved = 1
            new_step["output"] = output
            steps.append(new_step)

        history_item["score"] = history["score"]
        history_item["step_counter"] = number_steps

        # Because Elastic doesn't allow table to go across indexes, adding some scene info here that will be useful
        if scene_folder:
            scene = load_json_file(scene_folder, history_item["name"] + "-debug.json")
            if scene:
                if("observation" in scene):
                    if(scene["observation"]):
                        history_item["category"] = "observation"
                        history_item["category_type"] = history_item["test_type"]
                    else:
                        history_item["category"] = "interactive"
                        type_parts = history_item["test_type"].rsplit('-', 1)
                        history_item["category_type"] = type_parts[1]
                        history_item["category_pair"] = type_parts[0]
                else:
                    history_item["category"] = "interactive"
                    type_parts = history_item["test_type"].rsplit('_', 1)
                    history_item["category_type"] = type_parts[1]
                    history_item["category_pair"] = type_parts[0]

                if(history_item["category"] == "interactive"):
                    if "score" not in history_item:
                        history_item["score"] = {}
                        history_item["score"]["classification"] = "end"
                        history_item["score"]["confidence"] = 0
                    history_item["score"]["score"] = interactive_goal_achieved
                    history_item["score"]["ground_truth"] = 1
                else:
                    if "score" in history_item:
                        history_item["score"]["score"] = 1 if history_item["score"]["classification"] == scene["answer"]["choice"] else 0
                        history_item["score"]["ground_truth"] = 1 if "plausible" == scene["answer"]["choice"] else 0
                    else:
                        history_item["score"] = {}
                        history_item["score"]["score"] = -1
                        history_item["score"]["ground_truth"] = 1 if "plausible" == scene["answer"]["choice"] else 0

                # Adjusting confidence for plausibility 
                if "confidence" in history_item["score"]:
                    if history_item["score"]["confidence"] == 1 and history_item["score"]["classification"] == "implausible":
                        history_item["score"]["adjusted_confidence"] = 0
                    elif history_item["score"]["classification"] == "implausible" and history_item["score"]["confidence"] > 0.5:
                        history_item["score"]["adjusted_confidence"] = 1 - history_item["score"]["confidence"]
                    elif history_item["score"]["confidence"] == 1:
                        history_item["score"]["adjusted_confidence"] = 1
                    else: 
                        history_item["score"]["adjusted_confidence"] = float(history_item["score"]["confidence"])

                    history_item["score"]["mse"] = math.pow((history_item["score"]["ground_truth"] - round(float("{0:.9f}".format(history_item["score"]["adjusted_confidence"])))), 2)

                # Psychologists wanted to see a definitive answer of correctness
                if history_item["score"]["score"] == 1:
                    history_item["score"]["score_description"] = "Correct"
                elif history_item["score"]["score"] == 0:
                    history_item["score"]["score_description"] = "Incorrect"
                elif history_item["score"]["score"] == -1:
                    history_item["score"]["score_description"] = "No answer"
                
        # Check for duplicate Mess History files that don't include any steps
        if steps:
            history_item["steps"] = steps
            ingest_history.append(history_item)
    
    ingest_to_mongo(HISTORY_INDEX, ingest_history)


def main(argv) -> None:
    parser = argparse.ArgumentParser(description='Ingest MCS Scene JSON files into Elasticsearch')
    parser.add_argument('--folder', required=True, help='Folder location of files to important')
    parser.add_argument('--eval_name', required=True, help='Name for this eval')
    parser.add_argument('--performer', required=False, help='Associate this ingest with a performer')
    parser.add_argument('--scene_folder', required=False, help='Path to folder to link scene history with scene')
    parser.add_argument('--type', required=True, help='Choose if ingesting scenes or history', choices=['scene', 'history'])

    args = parser.parse_args(argv[1:])

    if args.type == 'scene':
        ingest_scene_files(args.folder, args.eval_name, args.performer)
    if args.type == 'history':
        ingest_history_files(args.folder, args.eval_name, args.performer, args.scene_folder)


if __name__ == '__main__':
    main(sys.argv)