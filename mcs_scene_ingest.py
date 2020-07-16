import json
import os
import re
import sys
import argparse
import math
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

COLOR_LIST = ["black","blue","brown","green","grey","orange","purple","red","white","yellow"]
MATERIAL_LIST = ["ceramic","food","glass","hollow","fabric","metal","organic","paper","plastic","rubber","soap","sponge","stone","wax","wood"]

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


def get_scene_name_from_history_file(file_name: str, regex_str: str) -> str:
    # Currently checking for the part of the file name before the data, we could remove this by adding
    #    the scene name into the history file at some point in a future ticket.
    reg = re.compile(regex_str)
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


def ingest_history_files(folder: str, eval_name: str, performer: str, scene_folder: str) -> None:
    history_files = find_history_files(folder)
    ingest_history = []

    for file in history_files:
        print("Ingest history files: {}".format(file))
        history = load_history_file(folder, file)

        history_item = {}
        history_item["eval"] = eval_name
        history_item["performer"] = performer
        history_item["name"] = get_scene_name_from_history_file(file, "-202.+-")
        history_item["testType"] = get_scene_name_from_history_file(history_item["name"], "-.+-")

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

        # Because Elastic doesn't allow table to go across indexes, adding some scene info here that will be useful
        if scene_folder:
            scene = load_scene_file(scene_folder, history_item["name"] + "-debug.json")
            if scene:
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
                        history_item["score"]["adjusted_confidence"] = history_item["score"]["confidence"]

                history_item["score"]["mse_loss"] = math.pow((history_item["score"]["ground_truth"] - round(float("{0:.9f}".format(history_item["score"]["score"])))), 2)

                # Psychologists wanted to see a definitive answer of correctness
                if history_item["score"]["score"] == 1:
                    history_item["score"]["score_description"] = "Correct"
                elif history_item["score"]["score"] == 0:
                    history_item["score"]["score_description"] = "Incorrect"
                elif history_item["score"]["score"] == -1:
                    history_item["score"]["score_description"] = "No answer"

                history_item["scene"] = {}
                history_item["scene"]["answer_choice"] = scene["answer"]["choice"]
                history_item["scene"]["category"] = scene["goal"]["category"]
                history_item["scene"]["domain_list"] = scene["goal"]["domain_list"]
                history_item["scene"]["type_list"] = scene["goal"]["type_list"]
                history_item["scene"]["task_list"] = scene["goal"]["task_list"]
                history_item["scene"]["info_list"] = scene["goal"]["info_list"]

                objects = []
                for scene_obj in scene["objects"]:
                    obj = {}
                    obj["type"] = scene_obj["type"]
                    obj["mass"] = scene_obj["mass"]
                    obj["info"] = scene_obj["info"]
                    obj["type"] = scene_obj["type"]

                    if "shape" in scene_obj:
                        obj["shape"] = scene_obj["shape"]
                    if "novel_color" in scene_obj:
                        obj["novel_color"] = scene_obj["novel_color"]
                    if "novel_combination" in scene_obj:
                        obj["novel_combination"] = scene_obj["novel_combination"]
                    if "novel_shape" in scene_obj:
                        obj["novel_shape"] = scene_obj["novel_shape"]
                    if "goal_string" in scene_obj:
                        obj["goal_string"] = scene_obj["goal_string"]

                        descriptors = []
                        obj_colors = []
                        obj_materials = []
                        goal_words = obj["goal_string"].split()
                        for obj_str in goal_words:
                            if obj_str in COLOR_LIST:
                                obj_colors.append(obj_str)
                            if obj_str in MATERIAL_LIST:
                                obj_materials.append(obj_str)

                        # Add color + shape to descriptors
                        if len(obj_colors) == 2: 
                            descriptors.append(obj_colors[0] + " " + obj["shape"])
                            descriptors.append(obj_colors[1] + " " + obj["shape"])
                            descriptors.append(obj_colors[0] + " " + obj_colors[1] + " " + obj["shape"])
                        elif len(obj_colors) == 1:
                            descriptors.append(obj_colors[0] + " " + obj["shape"])

                        # Add material + shape to descriptors
                        if len(obj_materials) == 2:
                            descriptors.append(obj_materials[0] + " " + obj["shape"])
                            descriptors.append(obj_materials[1] + " " + obj["shape"])
                            descriptors.append(obj_materials[0] + " " + obj_materials[1] + " " + obj["shape"])
                        elif len(obj_materials) == 1:
                            descriptors.append(obj_materials[0] + " " + obj["shape"])

                        # Add color + materials + shape to descriptors
                        full_str = ""
                        for color in obj_colors:
                            full_str = full_str + color + " "
                        for material in obj_materials:
                            full_str = full_str + material + " "

                        if len(full_str) > 0:
                            descriptors.append(full_str + obj["shape"])
                            obj["descriptors"] = descriptors

                    if "intphys_option" in scene_obj:
                        if "is_occluder" in scene_obj["intphys_option"]:
                            obj["is_occluder"] = scene_obj["intphys_option"]["is_occluder"] 

                    objects.append(obj)

                # For determining the counts of different objects "context", "occluders", and "objects"
                num_objects = 0
                history_item["scene"]["has_novel_color"] = "False"
                history_item["scene"]["has_novel_shape"] = "False"
                history_item["scene"]["has_novel_combination"] = "False"
                for item in history_item["scene"]["type_list"]:
                    if "background objects" in item:
                        history_item["scene"]["num_context_objects"] = int(item[-2:])
                    if "occluders" in item:
                        history_item["scene"]["num_occluders"] = int(item[-2:])
                    if "walls" in item:
                        history_item["scene"]["num_interior_walls"] = int(item[-2:])
                    if "obstructors" in item:
                        history_item["scene"]["num_obstructors"] = int(item[-2:])
                    if "confusors" in item:
                        history_item["scene"]["num_confusors"] = int(item[-2:])
                    if "distractor novel color" in item or "target novel color" in item or "confusor novel color" in item or "obstructor novel color" in item:
                        history_item["scene"]["has_novel_color"] = "True"
                    if "distractor novel shape" in item or "target novel shape" in item or "confusor novel shape" in item or "obstructor novel shape" in item:
                        history_item["scene"]["has_novel_shape"] = "True"
                    if "distractor novel combination" in item or "target novel combination" in item or "confusor novel combination" in item or "obstructor novel combination" in item:
                        history_item["scene"]["has_novel_combination"] = "True"
                    if "targets" in item:
                        num_objects += int(item[-2:])
                    if "distractors" in item:
                        num_objects += int(item[-2:])
                
                history_item["scene"]["num_objects"] = num_objects
                history_item["scene"]["objects"] = objects
                
        # Check for duplicate Mess History files that don't include any steps
        if steps:
            history_item["steps"] = steps

            ingest_history.append(get_index_dict(HISTORY_INDEX, HISTORY_TYPE))
            ingest_history.append(history_item)

    ingest_elastic_search("mcs_history", eval_name, False, mcs_scene_history_schema.get_scene_history_schema(), ingest_history)


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