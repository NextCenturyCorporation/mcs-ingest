import argparse
import io
import json
import logging
import os
import math
import sys
from collections.abc import MutableMapping
from typing import List

from pymongo import MongoClient

import create_collection_keys
# We might want to move mongo user/pass to new file
from scorecard.scorecard import Scorecard

# Currently just removing image mag from scene files, might
#    wish to move more keys, or remove so much from the schema
#    that we want to just map the fields we want to the schema
KEYS_TO_DELETE = [
    'image',
    'debug'
]

SCENE_INDEX = "mcs_scenes"
HISTORY_INDEX = "mcs_history"

# Convert names used in config to 'pretty' names for UI
TEAM_MAPPING_DICT = {
    "mess": "MESS",
    # Leaving the mit flag for backwards compatibility for now.
    "mit": "IBM-MIT-Harvard-Stanford",
    "cora": "CORA",
    "opics": "OPICS",
    "baseline": "TA2 Baseline"
}

# Convert Eval names used to 'pretty' history record names for UI
EVAL_HIST_MAPPING_DICT = {
    "eval_3-5": "Evaluation 3.5 Results",
    "eval_3-75": "Evaluation 3.75 Results",
    "eval_4": "Evaluation 4 Results",
    "eval_5": "Evaluation 5 Results",
    "eval_6": "Evaluation 6 Results",
    "eval_7": "Evaluation 7 Results",
    "eval_8": "Evaluation 8 Results",
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

# Weight from Design, some plausible scenes are worth more,
#   because there aren't as many as the implausible ones
SHAPE_CONSTANCY_DUPLICATE_CUBE = ["A1", "B1"]
SHAPE_CONSTANCY_8X_CUBE = ["A2", "B2", "C2", "D2"]

MAX_XY_VIOLATIONS = 50
SCENE_DEBUG_EXTENSION = "_debug.json"

# Temporary Reorientation Scoring Variables
# Todo:  Move scoring to MCS api
FRONT_RIGHT_CORNER = {"x": 6, "z": 4, "name": "front_right"}
FRONT_LEFT_CORNER = {"x": -6, "z": 4, "name": "front_left"}
BACK_RIGHT_CORNER = {"x": 6, "z": -4, "name": "back_right"}
BACK_LEFT_CORNER = {"x": -6, "z": -4, "name": "back_left"}
DISTANCE_FROM_CORNER = 1.5
STEP_TO_CHECK_CORNER = 550
POSSIBLE_CORNERS = [
    FRONT_RIGHT_CORNER,
    FRONT_LEFT_CORNER,
    BACK_RIGHT_CORNER,
    BACK_LEFT_CORNER]


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
    new_scene = {}
    for key, value in scene.items():
        if key not in set(keys):
            if isinstance(value, MutableMapping):
                new_scene[key] = delete_keys_from_scene(value, set(keys))
            else:
                new_scene[key] = value

    return new_scene


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


def find_history_files(folder: str, extension: str) -> dict:
    history_files = [
        f for f in os.listdir(
            folder) if str(f).endswith("." + extension)]
    history_files.sort()
    return history_files


def build_scene_item(file_name: str, folder: str, eval_name: str) -> dict:
    logging.info(f"Ingest scene file: {file_name}")
    scene = load_json_file(folder, file_name)

    if eval_name is None:
        scene["eval"] = scene["debug"]["evaluation"]
        eval_name = scene["debug"]["evaluation"]
    else:
        scene["eval"] = eval_name

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

    # Add Keys when a new evluation item is created
    collection_count = collection.find(
        {"evaluation": scene_item["eval"]}).count()
    if collection_count == 1:
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

    client = MongoClient(
        'mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
    mongoDB = client['mcs']

    ingest_to_mongo(SCENE_INDEX, ingest_scenes, client)

    create_collection_keys.find_collection_keys(
        SCENE_INDEX, eval_name, mongoDB)


def determine_evaluation_hist_name(
        eval_name: str, history_eval_name: str) -> str:
    eval_str = ""
    if eval_name is None:
        if history_eval_name in EVAL_HIST_MAPPING_DICT:
            eval_str = EVAL_HIST_MAPPING_DICT[history_eval_name]
        else:
            eval_str = history_eval_name
    else:
        eval_str = eval_name
    return eval_str


def determine_evaluation_scene_name(history_eval_name: str) -> str:
    eval_str = ""
    if history_eval_name in EVAL_SCENE_MAPPING_DICT:
        eval_str = EVAL_SCENE_MAPPING_DICT[history_eval_name]
    else:
        eval_str = history_eval_name
    return eval_str


def determine_team_mapping_name(info_team: str) -> str:
    name_str = ""
    if info_team in TEAM_MAPPING_DICT:
        name_str = TEAM_MAPPING_DICT[info_team]
    else:
        # Add code to convert something like mess2 to MESS2
        name_str = info_team.upper()
    return name_str


def check_agent_to_corner_position(
        position: dict,
        incorrect_corners: List[dict],
        correct_corners: List[dict],
        corner_visit_order: List[dict]) -> List[dict]:

    corner_visited = None

    # Check if agent is close to any corner
    for corner in POSSIBLE_CORNERS:
        if math.dist(
                [position["x"], position["z"]],
                [corner["x"], corner["z"]]) < DISTANCE_FROM_CORNER:
            corner_visited = corner

    # Return if not near a corner, or still near last corner
    if (corner_visited is None or (
            len(corner_visit_order) > 0 and
            corner_visit_order[-1]["name"] == corner_visited["name"])):
        return corner_visit_order

    if corner_visited in incorrect_corners:
        corner_visit_order.append({
            "name": corner_visited["name"],
            "type": "incorrect"
        })

    if corner_visited in correct_corners:
        # Corners get added to correct list, first is always correct
        #   Second corner is always ambiguous corner
        corner_type = "correct" if (
            corner_visited["name"] == correct_corners[0]["name"]) else (
                "neutral")
        corner_visit_order.append({
            "name": corner_visited["name"],
            "type": corner_type
        })

    return corner_visit_order


def build_new_step_obj(
        step: dict,
        interactive_reward: int,
        interactive_goal_achieved: int,
        number_steps: int,
        incorrect_corners: List[dict],
        correct_corners: List[dict],
        corner_visit_order: List[dict],
        reorientation_scoring_override: bool) -> tuple:
    new_step = {}
    new_step["stepNumber"] = step["step"]
    new_step["action"] = step["action"]
    new_step["args"] = step["args"]
    new_step["classification"] = step["classification"]
    new_step["confidence"] = step["confidence"]
    new_step["internal_state"] = step["internal_state"]

    # TODO: Added if check because key error in 3.75 and earlier
    if "delta_time_millis" in step:
        new_step["delta_time_millis"] = step["delta_time_millis"]

    # If too many items in violations_xy_list, take the first 50
    if (step["violations_xy_list"] and isinstance(
            step["violations_xy_list"], list) and
            len(step["violations_xy_list"]) > MAX_XY_VIOLATIONS):
        new_step["violations_xy_list"] = \
            step["violations_xy_list"][:MAX_XY_VIOLATIONS]
    else:
        new_step["violations_xy_list"] = step["violations_xy_list"]

    output = {}
    if ("output" in step):
        if (
                reorientation_scoring_override and
                number_steps > STEP_TO_CHECK_CORNER):
            corner_visit_order = check_agent_to_corner_position(
                step["output"]["position"],
                incorrect_corners,
                correct_corners,
                corner_visit_order)

        output["return_status"] = step["output"]["return_status"]
        output["reward"] = step["output"]["reward"]
        # TODO: Added if check because key error in 3.75 and earlier
        if "physics_frames_per_second" in step["output"]:
            output["physics_frames_per_second"] = step[
                "output"]["physics_frames_per_second"]
        interactive_reward = output["reward"]
        if (
                output["reward"] >= (
                    0 - ((number_steps - 1) * 0.001) + 1)):
            interactive_goal_achieved = 1
    new_step["output"] = output

    return (
        new_step,
        interactive_reward,
        interactive_goal_achieved,
        corner_visit_order)


def add_weighted_cube_scoring(history_item: dict, scene: dict) -> tuple:
    weighted_score, weighted_score_worth, weighted_confidence = 0, 0, 0
    if "goal" in scene:
        if "sceneInfo" in scene["goal"]:
            if scene["goal"]["sceneInfo"]["tertiaryType"] == "shape constancy":
                if history_item["scene_goal_id"] in \
                        SHAPE_CONSTANCY_DUPLICATE_CUBE:
                    weighted_score = history_item["score"]["score"] * 2
                    weighted_score_worth = 2
                    weighted_confidence = float(
                        history_item["score"]["confidence"]) * 2
                elif history_item["scene_goal_id"] in SHAPE_CONSTANCY_8X_CUBE:
                    weighted_score = history_item["score"]["score"] * 8
                    weighted_score_worth = 8
                    weighted_confidence = float(
                        history_item["score"]["confidence"]) * 8
                else:
                    weighted_score = history_item["score"]["score"]
                    weighted_score_worth = 1
                    weighted_confidence = history_item["score"]["confidence"]
            else:
                weighted_score = history_item["score"]["score"]
                weighted_score_worth = 1
                weighted_confidence = history_item["score"]["confidence"]
    return (weighted_score, weighted_score_worth, weighted_confidence)


def calc_scorecard(history_item: dict, scene: dict) -> dict:
    scorecard = Scorecard(history_item, scene)
    scorecard_vals = scorecard.score_all()
    return scorecard_vals


def calculate_reorientation_true_score(
        corner_visit_order: List[dict],
        interactive_goal_achieved: int) -> int:
    # This is correct if the agent goes to the correct corner first
    if(len(corner_visit_order) > 0):
        return 1 if corner_visit_order[0].type == "correct" else 0
    else:
        return interactive_goal_achieved


def calculate_reorientation_score(
        corner_visit_order: List[dict],
        interactive_goal_achieved: int) -> int:
    # This is correct if they get to the correct corner before ever
    #  going to an incorrect corner, so they could go to an
    #  ambiguous/neutral corner first and still be correct
    if(len(corner_visit_order) > 0):
        correct_corner_achieved = 1
        # loop through corners, ignore neutral corner, if come to
        #   incorrect corner before correct, set it false and exit
        #   loop, if come to correct first, exit loop, correct score
        for corner in corner_visit_order:
            if corner["type"] == "incorrect":
                correct_corner_achieved = 0
                break
            if corner["type"] == "correct":
                break
        return correct_corner_achieved
    else:
        return interactive_goal_achieved


def process_score(
        history_item: dict,
        scene: dict,
        interactive_goal_achieved: int,
        interactive_reward: int,
        corner_visit_order: List[dict],
        reorientation_scoring_override: bool) -> dict:
    # Removed Adjusted Confidence, should be OBE
    if (history_item["category"] == "interactive"):
        if "score" not in history_item:
            history_item["score"] = {}
            history_item["score"]["classification"] = "end"
            history_item["score"]["confidence"] = 0
        history_item["score"]["goal_achieved"] = interactive_goal_achieved
        # TO DO
        if reorientation_scoring_override:
            history_item["score"]["goal_achieved"] = (
                calculate_reorientation_true_score(
                    corner_visit_order, interactive_goal_achieved))
            history_item["score"]["score"] = 1 if (
                corner_visit_order[0]["type"] != "incorrect") else 0
        else:
            history_item["score"]["score"] = interactive_goal_achieved
            history_item["score"]["goal_achieved"] = interactive_goal_achieved
        history_item["score"]["reward"] = interactive_reward
        history_item["score"]["ground_truth"] = 1
    else:
        if "score" in history_item:
            history_item["score"]["score"] = 1 if \
                history_item["score"]["classification"] == \
                scene["goal"]["answer"]["choice"] else 0
            history_item["score"]["ground_truth"] = 1 if \
                ("plausible" == scene["goal"]["answer"]["choice"] or
                 "expected" == scene["goal"]["answer"]["choice"]) else 0
        else:
            # Eval 2 backwards compatiblity
            history_item["score"] = {}
            history_item["score"]["score"] = -1
            history_item["score"]["ground_truth"] = 1 if "plausible" == scene[
                "answer"]["choice"] else 0

    # Psychologists wanted to see a definitive answer of correctness
    if history_item["score"]["score"] == 1:
        history_item["score"]["score_description"] = "Correct"
    elif history_item["score"]["score"] == 0:
        history_item["score"]["score_description"] = "Incorrect"
    elif history_item["score"]["score"] == -1:
        history_item["score"]["score_description"] = "No answer"

    # Calculate Cube Weighted Scoring
    (
        weighted_score,
        weighted_score_worth,
        weighted_confidence
    ) = add_weighted_cube_scoring(history_item, scene)

    history_item["score"]["weighted_score"] = weighted_score
    history_item["score"]["weighted_score_worth"] = weighted_score_worth
    history_item["score"]["weighted_confidence"] = weighted_confidence

    return history_item["score"]


def reorientation_calculate_corners(scene: dict) -> List[dict]:
    correct_corners = [scene["goal"]["sceneInfo"]["corner"]]

    if scene["goal"]["sceneInfo"]["ambiguous"]:
        correct_corner_parts = correct_corners[0].split("_")
        ambigous_corner_part1 = "front" if (
            correct_corner_parts[0] == "back") else "back"
        ambigous_corner_part2 = "left" if (
            correct_corner_parts[1] == "right") else "right"
        correct_corners.append(
            ambigous_corner_part1 + "_" + ambigous_corner_part2)

    return ([corner for corner in POSSIBLE_CORNERS if (
        not corner["name"] in correct_corners)],
        [corner for corner in POSSIBLE_CORNERS if (
            corner["name"] in correct_corners)])


def build_history_item(
        history_file: str,
        folder: str,
        eval_name: str,
        performer: str,
        scene_folder: str,
        extension: str,
        client: MongoClient,
        db_string: str) -> dict:
    logging.info(f"Ingest history file: {history_file}")
    mongoDB = client[db_string]

    # Create History Object and add basic information
    history = load_json_file(folder, history_file)

    history_item = {}
    history_item["eval"] = determine_evaluation_hist_name(
        eval_name,
        history["info"]["evaluation_name"]
    )
    history_item["performer"] = determine_team_mapping_name(
        history["info"]["team"])
    history_item["name"] = history["info"]["name"]
    history_item["metadata"] = history["info"]["metadata"]
    history_item["fullFilename"] = os.path.splitext(history_file)[0]
    history_item["fileTimestamp"] = history["info"]["timestamp"]
    history_item["score"] = history["score"]

    # Load Scene from Database or File
    scene = None
    if scene_folder is None:
        collection = mongoDB[SCENE_INDEX]
        scene_rec_name = determine_evaluation_scene_name(
            history["info"]["evaluation_name"]
        )
        scene = collection.find_one(
            {"name": history_item["name"], "eval": scene_rec_name})
    else:
        scene = load_json_file(
            scene_folder, history_item["name"] + SCENE_DEBUG_EXTENSION)

    # This variable will override any rewards for a reorientation task
    #    should the agent visit a corner it should not be at
    reorientation_scoring_override = (
        scene["goal"]["sceneInfo"]["tertiaryType"] == "reorientation")

    # set all corners incorrect at beginning of scene
    (
        incorrect_corners,
        correct_corners
    ) = reorientation_calculate_corners(scene) if (
        reorientation_scoring_override) else ([], [])

    corner_visit_order = []

    # Loop through and process steps
    steps = []
    number_steps = 0
    interactive_goal_achieved = 0
    interactive_reward = 0

    for step in history["steps"]:
        number_steps += 1
        (
            new_step,
            interactive_reward,
            interactive_goal_achieved,
            corner_visit_order
        ) = build_new_step_obj(
            step,
            interactive_reward,
            interactive_goal_achieved,
            number_steps,
            incorrect_corners,
            correct_corners,
            corner_visit_order,
            reorientation_scoring_override)
        steps.append(new_step)

    history_item["steps"] = steps
    history_item["step_counter"] = number_steps
    history_item["corner_visit_order"] = corner_visit_order

    if scene:
        # Add some basic scene information into history object to make
        #    UI load times faster then having to query scene every time
        if scene_folder is None:
            history_item["scene_num"] = scene["scene_num"]
            history_item["test_num"] = scene["test_num"]
        else:
            history_item["scene_num"] = scene["debug"]["sceneNumber"]
            history_item["test_num"] = scene["debug"]["hypercubeNumber"]

        history_item["scene_goal_id"] = scene["goal"]["sceneInfo"]["id"][0]
        history_item["test_type"] = scene["goal"]["sceneInfo"]["secondaryType"]
        history_item["category"] = scene["goal"]["sceneInfo"]["primaryType"]
        history_item["hasNovelty"] = scene["goal"][
            "sceneInfo"]["untrained"]["any"]

        if scene["goal"]["sceneInfo"]["secondaryType"] == "retrieval":
            history_item["category_type"] = \
                scene["goal"]["sceneInfo"]["secondaryType"] + \
                "_" + scene["goal"]["sceneInfo"]["tertiaryType"]
        else:
            history_item["category_type"] = scene[
                "goal"]["sceneInfo"]["tertiaryType"]

        history_item["score"] = process_score(
            history_item,
            scene,
            interactive_goal_achieved,
            interactive_reward,
            corner_visit_order,
            reorientation_scoring_override)
        history_item["score"]["scorecard"] = calc_scorecard(history, scene)

        return history_item


def automated_history_ingest_file(
        history_file: str,
        folder: str,
        db_string: str) -> None:
    client = MongoClient(
        'mongodb://mongomcs:mongomcspassword@localhost:27017/' + db_string)
    mongoDB = client[db_string]

    history_item = build_history_item(
        history_file, folder, None, None, None, "json", client, db_string)
    collection = mongoDB[HISTORY_INDEX]
    check_exists = collection.find(
        {
            "name": history_item["name"],
            "eval": history_item["eval"],
            "performer": history_item["performer"],
            "metadata": history_item["metadata"]
        }
    )

    if check_exists.count() == 0:
        logging.info(f"Inserting {history_item['name']}")
        collection.insert_one(history_item)
    else:
        for item in check_exists:
            if history_item["fileTimestamp"] > item["fileTimestamp"]:
                logging.info(f"Updating {history_item['name']}")
                collection.replace_one({"_id": item["_id"]}, history_item)

    # Add Keys when a new evluation item is created
    collection_count = collection.find(
        {"eval": history_item["eval"]}).count()
    if collection_count == 1:
        create_collection_keys.find_collection_keys(
            HISTORY_INDEX, history_item["eval"], mongoDB)


def ingest_history_files(
        folder: str,
        eval_name: str,
        performer: str,
        scene_folder: str,
        extension: str) -> None:
    client = MongoClient(
        'mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
    mongoDB = client['mcs']

    history_files = find_history_files(folder, extension)
    ingest_history = []

    for file in history_files:
        history_item = build_history_item(
            file,
            folder,
            eval_name,
            performer,
            scene_folder,
            extension,
            client,
            'mcs')

        replacementIndex = -1
        for index, item in enumerate(ingest_history):
            if item["fullFilename"] == history_item["fullFilename"]:
                if history_item["fileTimestamp"] > item["fileTimestamp"]:
                    replacementIndex = index

        if replacementIndex == -1:
            ingest_history.append(history_item)
        else:
            ingest_history[replacementIndex] = history_item

    ingest_to_mongo(HISTORY_INDEX, ingest_history, client)

    create_collection_keys.find_collection_keys(
        HISTORY_INDEX, eval_name, mongoDB)


def main(argv) -> None:
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
    parser.add_argument(
        '--type',
        required=True,
        help='Choose if ingesting scenes or history',
        choices=['scene', 'history'])
    parser.add_argument(
        '--extension',
        required=False,
        help='History file extension for legacy ingest')

    args = parser.parse_args(argv[1:])
    extension = args.extension
    if extension is None:
        extension = "json"

    if args.type == 'scene':
        ingest_scene_files(args.folder, args.eval_name)
    if args.type == 'history':
        ingest_history_files(
            args.folder,
            args.eval_name,
            args.performer,
            args.scene_folder,
            extension
        )


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main(sys.argv)
