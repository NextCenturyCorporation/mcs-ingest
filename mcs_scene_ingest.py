import json
import os
import re
import sys
import argparse
import math
import io

from collections.abc import MutableMapping 
from pymongo import MongoClient

# We might want to move mongo user/pass to new file
client = MongoClient('mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
mongoDB = client['mcs']

# Currently just removing image mag from scene files, might wish to move more keys, 
#    or remove so much from the schema that we want to just map the fields we want to the schema
KEYS_TO_DELETE = ['image', 'sequenceNumber', 'hypercubeNumber', 'sceneNumber']

SCENE_INDEX = "mcs_scenes"
HISTORY_INDEX = "mcs_history"

TEAM_MAPPING_DICT = {
    "mess": "MESS-UCBerkeley",
    "mit": "IBM-MIT-Harvard-Stanford",
    "opics": "OPICS (OSU, UU, NYU)",
    "baseline": "Baseline"
}

OBJ_PERM_DUPLICATE_CUBE = ["S1", "T1", "U1"]
OBJ_PERM_8X_CUBE = ["S2", "T2", "U2", "V2", "W2", "X2", "Y2", "Z2", "AA2"]
SPATIO_TEMP_ELIMINATE_CUBE = ["A1", "A2", "A3", "A4", "D1", "D2", "D3", "D4", "G1", "G2", "G3", "G4",
    "J1", "J2", "J3", "J4", "M1", "M2", "M3", "M4", "P1", "P2", "P3", "P4"]
SHAPE_CONSTANCY_DUPLICATE_CUBE = ["A1", "B1"]
SHAPE_CONSTANCY_8X_CUBE = ["A2", "B2", "C2", "D2"]


def load_json_file(folder: str, file_name: str) -> dict:
    with io.open(os.path.join(folder, file_name), mode='r', encoding='utf-8-sig') as json_file:
        return json.loads(json_file.read())


def load_history_text_file(folder: str, file_name: str) -> dict:
    # For loading Eval 2 history files which are txt files and not
    #    properly formatted json
    with open(os.path.join(folder, file_name)) as file:
        no_line_breaks = file.read().replace("\n", "")
        data = "[" + no_line_breaks.replace('}{', '},{') + "]"
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

    # ----- Moving to create_keys_script that will run after ingestion -----
    # Loop through documents to generate a keys collection to help
    #   speed in loading keys in UI
    # keys = []
    # documents = collection.find()
    # for doc in documents:
    #     recursive_find_keys(doc, keys, "")

    # keys_dict = {}
    # keys_dict["keys"] = keys

    # collection = mongoDB[index + "_keys"]
    # collection.drop()
    # result = collection.insert_one(keys_dict)
    # print(result)


def find_scene_files(folder: str) -> dict:
    scene_files = [f for f in os.listdir(folder) if str(f).endswith("debug.json")]
    if not scene_files:
        # For ingesting files that we generated before we started generating debug files (i.e. - Interaction Training Data)
        scene_files = [f for f in os.listdir(folder) if str(f).endswith(".json")]
    scene_files.sort()
    return scene_files


def find_history_files(folder: str, extension: str) -> dict:
    history_files = [f for f in os.listdir(folder) if str(f).endswith("." + extension)]
    history_files.sort()
    return history_files


def get_index_dict(index: str, index_type: str) -> dict:
    return {
        "index": {
            "_index": index,
            "_type": index_type
        }
    }


def get_scene_name_from_history_text_file(file_name: str, regex_str: str) -> str:
    # Currently checking for the part of the file name before the data, do not remove
    #   we need this to ingest legacy eval 2 files
    reg = re.compile(regex_str)
    for match in re.finditer(reg, file_name):
        return file_name[0:match.start()]


def ingest_scene_files(folder: str, eval_name: str, performer: str) -> None:
    scene_files = find_scene_files(folder)
    ingest_scenes = []

    for file in scene_files:
        print("Ingest scene file: {}".format(file))
        scene = load_json_file(folder, file)
        scene["eval"] = eval_name
        scene["performer"] = performer
        if "2" in eval_name:
            scene["test_type"] = scene["name"][:-7]
            scene["test_num"] = int(scene["name"][-6:-2])
            scene["scene_num"] = int(scene["name"][-1:])
        else:
            if "sequenceNumber" in scene:
                scene["test_num"] = scene["sequenceNumber"]
            else:
                scene["test_num"] = scene["hypercubeNumber"]
            scene["scene_num"] = scene["sceneNumber"]
            if "sequenceId" in scene["goal"]["sceneInfo"]:
                scene["goal"]["sceneInfo"]["hypercubeId"] = scene["goal"]["sceneInfo"]["sequenceId"]
                del scene["goal"]["sceneInfo"]["sequenceId"]
        scene = delete_keys_from_scene(scene, KEYS_TO_DELETE)
        ingest_scenes.append(scene)

    ingest_to_mongo(SCENE_INDEX, ingest_scenes)


def ingest_history_files(folder: str, eval_name: str, performer: str, scene_folder: str, extension: str) -> None:
    history_files = find_history_files(folder, extension)
    ingest_history = []
    SCENE_DEBUG_EXTENSION = "_debug.json"

    for file in history_files:
        print("Ingest history files: {}".format(file))
        history = {}

        # Legacy Eval 2 History files will be txt files and not json
        if extension == 'txt':
            history = load_history_text_file(folder, file)
        else:
            history = load_json_file(folder, file)

        history_item = {}
        history_item["eval"] = eval_name

        # Legacy Eval 2 History files will be txt files and not json
        if extension == 'txt':
            history_item["performer"] = performer
            history_item["name"] = get_scene_name_from_history_text_file(file, "-202.+-")
            SCENE_DEBUG_EXTENSION = "-debug.json"
            history_item["test_type"] = history_item["name"][:-7]
            history_item["test_num"] = int(history_item["name"][-6:-2])
            history_item["scene_num"] = int(history_item["name"][-1:])
            history_item["url_string"] = ("eval=" + history_item["eval"] + "&test_type=" + history_item["test_type"] +
                                         "&test_num=" + str(history_item["test_num"]) + "&scene=" + str(history_item["scene_num"]))
        else: 
            history_item["performer"] = TEAM_MAPPING_DICT[history["info"]["team"]]
            history_item["name"] = history["info"]["name"]
            history_item["metadata"] = history["info"]["metadata"]
            history_item["fullFilename"] = os.path.splitext(file)[0]
            fileNameParts = history_item["fullFilename"].split("-", 1)
            history_item["filename"] = fileNameParts[0]
            history_item["fileTimestamp"] = fileNameParts[1]

        history_item["flags"] = {}
        history_item["flags"]["remove"] = False
        history_item["flags"]["interest"] = False

        steps = []
        number_steps = 0
        interactive_goal_achieved = 0
        interactive_reward = 0

        # Legacy Eval 2 History files will be txt files and not json
        if extension == 'txt':
            for step in history:
                if "step" in step:
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
                if "classification" in step:
                    history_item["score"] = {}
                    history_item["score"]["classification"] = step["classification"]
                    history_item["score"]["confidence"] = step["confidence"]
        else:
            for step in history["steps"]:
                number_steps += 1
                new_step = {}
                new_step["stepNumber"] = step["step"]
                new_step["action"] = step["action"]
                new_step["args"] = step["args"]
                new_step["classification"] = step["classification"]
                new_step["confidence"] = step["confidence"]
                new_step["violations_xy_list"] = step["violations_xy_list"]
                output = {}
                if("output" in step):
                    output["return_status"] = step["output"]["return_status"]
                    output["reward"] = step["output"]["reward"]
                    interactive_reward = output["reward"]
                    if(output["reward"] >= (0 - ((number_steps-1) * 0.001) + 1)):
                        interactive_goal_achieved = 1
                new_step["output"] = output
                steps.append(new_step)

            history_item["score"] = history["score"]
        
        history_item["step_counter"] = number_steps

        # Because Elastic doesn't allow table to go across indexes, adding some scene info here that will be useful
        if scene_folder:
            scene = load_json_file(scene_folder, history_item["name"] + SCENE_DEBUG_EXTENSION)
            if scene:
                # For eval 3 going forward
                if "test_type" not in history_item:
                    history_item["scene_num"] = scene["sceneNumber"]
                    if "sequenceNumber" in scene:
                        history_item["test_num"] = scene["sequenceNumber"]
                    else: 
                        history_item["test_num"] = scene["hypercubeNumber"]
                    history_item["scene_goal_id"] = scene["goal"]["sceneInfo"]["id"][0]
                    history_item["test_type"] = scene["goal"]["sceneInfo"]["secondaryType"]
                    history_item["category"] = scene["goal"]["sceneInfo"]["primaryType"] 
                    if scene["goal"]["sceneInfo"]["tertiaryType"] == "retrieval":
                        history_item["category_type"] = scene["goal"]["sceneInfo"]["name"][:-3]
                    else:
                        history_item["category_type"] = scene["goal"]["sceneInfo"]["tertiaryType"]
                    history_item["url_string"] = ("eval=" + history_item["eval"] + "&category_type=" + history_item["category_type"] +
                        "&test_num=" + str(history_item["test_num"]) + "&scene=" + str(history_item["scene_num"]))
                # For eval 2 
                else:
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
                    history_item["score"]["reward"] = interactive_reward
                    history_item["score"]["ground_truth"] = 1
                else:
                    if "score" in history_item:
                        if "answer" in scene: 
                            history_item["score"]["score"] = 1 if history_item["score"]["classification"] == scene["answer"]["choice"] else 0
                            history_item["score"]["ground_truth"] = 1 if "plausible" == scene["answer"]["choice"] else 0
                        else:
                            history_item["score"]["score"] = 1 if history_item["score"]["classification"] == scene["goal"]["answer"]["choice"] else 0
                            history_item["score"]["ground_truth"] = 1 if ("plausible" == scene["goal"]["answer"]["choice"]
                                or "expected" == scene["goal"]["answer"]["choice"]) else 0
                    else:
                        history_item["score"] = {}
                        history_item["score"]["score"] = -1
                        history_item["score"]["ground_truth"] = 1 if "plausible" == scene["answer"]["choice"] else 0

                # Adjusting confidence for plausibility 
                if "confidence" in history_item["score"]:
                    if history_item["score"]["confidence"] == 1 and history_item["score"]["classification"] == "implausible":
                        history_item["score"]["adjusted_confidence"] = 0
                    elif history_item["score"]["classification"] == "implausible" and float(history_item["score"]["confidence"]) > 0.5:
                        history_item["score"]["adjusted_confidence"] = 1 - float(history_item["score"]["confidence"])
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

                # Add Cube Weighted Scoring Here
                if "goal" in scene:
                    if "sceneInfo" in scene["goal"]:
                        if scene["goal"]["sceneInfo"]["tertiaryType"] == "object permanence":
                            if history_item["scene_goal_id"] in OBJ_PERM_DUPLICATE_CUBE:
                                history_item["score"]["weighted_score"] = history_item["score"]["score"] * 2
                                history_item["score"]["weighted_score_worth"] = 2
                                history_item["score"]["weighted_confidence"] = float(history_item["score"]["confidence"]) * 2
                            elif history_item["scene_goal_id"] in OBJ_PERM_8X_CUBE:
                                history_item["score"]["weighted_score"] = history_item["score"]["score"] * 8
                                history_item["score"]["weighted_score_worth"] = 8
                                history_item["score"]["weighted_confidence"] = float(history_item["score"]["confidence"]) * 8
                            else:
                                history_item["score"]["weighted_score"] = history_item["score"]["score"]
                                history_item["score"]["weighted_score_worth"] = 1
                                history_item["score"]["weighted_confidence"] = history_item["score"]["confidence"]
                        elif scene["goal"]["sceneInfo"]["tertiaryType"] == "shape constancy":
                            if history_item["scene_goal_id"] in SHAPE_CONSTANCY_DUPLICATE_CUBE:
                                history_item["score"]["weighted_score"] = history_item["score"]["score"] * 2
                                history_item["score"]["weighted_score_worth"] = 2
                                history_item["score"]["weighted_confidence"] = float(history_item["score"]["confidence"]) * 2
                            elif history_item["scene_goal_id"] in SHAPE_CONSTANCY_8X_CUBE:
                                history_item["score"]["weighted_score"] = history_item["score"]["score"] * 8
                                history_item["score"]["weighted_score_worth"] = 8
                                history_item["score"]["weighted_confidence"] = float(history_item["score"]["confidence"]) * 8
                            else:
                                history_item["score"]["weighted_score"] = history_item["score"]["score"]
                                history_item["score"]["weighted_score_worth"] = 1
                                history_item["score"]["weighted_confidence"] = history_item["score"]["confidence"]
                        elif scene["goal"]["sceneInfo"]["tertiaryType"] == "spatio temporal continuity":
                            if history_item["scene_goal_id"] in SPATIO_TEMP_ELIMINATE_CUBE:
                                history_item["score"]["weighted_score"] = 0
                                history_item["score"]["weighted_score_worth"] = 0
                                history_item["score"]["weighted_confidence"] = 0
                            else:
                                history_item["score"]["weighted_score"] = history_item["score"]["score"]
                                history_item["score"]["weighted_score_worth"] = 1
                                history_item["score"]["weighted_confidence"] = history_item["score"]["confidence"]
                        else:
                            history_item["score"]["weighted_score"] = history_item["score"]["score"]
                            history_item["score"]["weighted_score_worth"] = 1
                            history_item["score"]["weighted_confidence"] = history_item["score"]["confidence"]
                    else:
                        history_item["score"]["weighted_score"] = history_item["score"]["score"]
                        history_item["score"]["weighted_score_worth"] = 1
                        if "confidence" in history_item["score"]:
                            history_item["score"]["weighted_confidence"] = history_item["score"]["confidence"]
                else:
                    history_item["score"]["weighted_score"] = history_item["score"]["score"]
                    history_item["score"]["weighted_score_worth"] = 1
                    history_item["score"]["weighted_confidence"] = history_item["score"]["confidence"]
                
        print(history_item["score"])
        # Check for duplicate Mess History files that don't include any steps
        if steps:
            history_item["steps"] = steps

            replacementIndex = -1
            for index, item in enumerate(ingest_history):
                if 'filename' in item and item["filename"] == history_item["filename"] and history_item["fileTimestamp"] > item["fileTimestamp"]:
                   replacementIndex = index

            if replacementIndex == -1:
                ingest_history.append(history_item)
            else:
                ingest_history[replacementIndex] = history_item

    ingest_to_mongo(HISTORY_INDEX, ingest_history)


def main(argv) -> None:
    parser = argparse.ArgumentParser(description='Ingest MCS Scene JSON files into Elasticsearch')
    parser.add_argument('--folder', required=True, help='Folder location of files to important')
    parser.add_argument('--eval_name', required=True, help='Name for this eval')
    parser.add_argument('--performer', required=False, help='Associate this ingest with a performer')
    parser.add_argument('--scene_folder', required=False, help='Path to folder to link scene history with scene')
    parser.add_argument('--type', required=True, help='Choose if ingesting scenes or history', choices=['scene', 'history'])
    parser.add_argument('--extension', required=False, help='History file extension for legacy ingest')

    args = parser.parse_args(argv[1:])
    extension = args.extension
    if extension is None:
        extension = "json"

    if args.type == 'scene':
        ingest_scene_files(args.folder, args.eval_name, args.performer)
    if args.type == 'history':
        ingest_history_files(args.folder, args.eval_name, args.performer, args.scene_folder, extension)


if __name__ == '__main__':
    main(sys.argv)