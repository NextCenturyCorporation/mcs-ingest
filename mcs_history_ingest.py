import argparse
import io
import json
import logging
import math
import os
import re

from typing import List, Union

from pymongo import MongoClient
import create_collection_keys

from scorecard import Scorecard


HISTORY_MAPPING_INDEX = "history_mapping"
SCENE_MAPPING_INDEX = "scenes_mapping"
SCENE_DEBUG_EXTENSION = "_debug.json"

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

# Weight from Design, some plausible scenes are worth more,
#   because there aren't as many as the implausible ones
SHAPE_CONSTANCY_DUPLICATE_CUBE = ["A1", "B1"]
SHAPE_CONSTANCY_8X_CUBE = ["A2", "B2", "C2", "D2"]
PASSIVE_OBJ_PERM_DUPLICATE_CUBE = ["G3", "H3", "I3"]

# Passing Weighting, everything besides these cube IDs will
#  be set to zero in the weight scoring.  This should all be 
#  moved to the scoring module when we refactor ingest
#  Support Relations and Solidity use all cube ids
PASSING_CELLS = {
    "agent identification": ["A1", "B1", "C1", "E1", "F1",
                             "G1", "A2", "B2", "C2", "E2",
                             "F2", "G2"],
    "spatial elimination": ["A1", "A2"],
    "moving target prediction": ["A1", "B1", "E1", "F1", "I1", "J1"],
    "holes": ["B1", "C1"],
    "lava": ["B1", "C1"],
    "ramp": ["B1", "C1", "E1", "F1", "H1", "I1", "K1", "L1"],
    "tool use": ["A1", "C1", "E1", "G1"],
    "interactive object permanence": ["A1", "C1"],
    "container": ["A1", "A2", "G1", "G2", "M1", "M2"],
    "obstacle": ["A1", "C1", "A2", "C2"],
    "occluder": ["A1", "A2", "C1", "C2", "E1", "E2", "G1",
                 "G2", "I1", "I2", "K1", "K2"],
    "gravity support": ["A1", "B1", "C1", "D1", "I1", "J1", "K1", "L1",
                        "M1", "N1", "O1", "P1", "S1", "T1", "W1", "X1",
                        "Y1", "Z1", "AA1", "CC1", "SS1", "TT1"]
}

MAX_XY_VIOLATIONS = 50

# Temporary Reorientation Scoring Variables
# TODO:  Move scoring to MCS api
DISTANCE_FROM_CORNER = 1.5
STEP_TO_CHECK_CORNER = 550
REORIENTATION_CORNERS = {
    'front_right': {'x': 6, 'z': 4},
    'front_left': {'x': -6, 'z': 4},
    'back_right': {'x': 6, 'z': -4},
    'back_left': {'x': -6, 'z': -4}
}


def get_history_collection(
        db_string: str,
        client: MongoClient,
        eval_name: str) -> str:
    mongoDB = client[db_string]
    collection = mongoDB[HISTORY_MAPPING_INDEX]
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

        collection_name = "eval_" + (str(eval_number)).replace(".", "_") + "_results"
        collection.insert_one({"name": eval_name, "collection": collection_name})
        return collection_name
    else:
        return mapping["collection"]


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


def determine_evaluation_hist_name(
        history_eval_name: str) -> str:
    return (
        EVAL_HIST_MAPPING_DICT[history_eval_name]
        if history_eval_name in EVAL_HIST_MAPPING_DICT
        else history_eval_name
    )


def return_agency_paired_history_item(
        client: MongoClient,
        db_string: str,
        history_item: dict) -> dict:
    mongoDB = client[db_string]
    collection_name = get_history_collection(db_string, client, history_item["eval"])
    collection = mongoDB[collection_name]
    return collection.find_one({
        "eval": history_item["eval"],
        "category_type": history_item["category_type"],
        "performer": history_item["performer"],
        "test_num": history_item["test_num"],
        "metadata": history_item["metadata"],
        "scene_num": 2 if history_item["scene_num"] == 1 else 1
    })


def update_agency_paired_history_item(
        client: MongoClient,
        db_string: str,
        history_item: dict) -> None:
    mongoDB = client[db_string]
    collection_name = get_history_collection(db_string, client, history_item["eval"])
    collection = mongoDB[collection_name]
    logging.info(f"Updating Agency Pair {history_item['name']}")
    collection.replace_one({"_id": history_item["_id"]}, history_item)


def process_score(
        history_item: dict,
        scene: dict,
        interactive_goal_achieved: int,
        interactive_reward: int,
        corner_visit_order: List[dict],
        reorientation_scoring_override: bool,
        client: MongoClient,
        db_string: str) -> dict:
    # Removed Adjusted Confidence, should be OBE
    if (history_item["category"] == "interactive"):
        if "score" not in history_item:
            history_item["score"] = {'classification': 'end', 'confidence': 0}
        history_item["score"]["goal_achieved"] = interactive_goal_achieved
        # TODO: Remove this scoring check when moving scoring to MCS api
        if reorientation_scoring_override:
            history_item["score"]["goal_achieved"] = (
                calculate_reorientation_true_score(
                    corner_visit_order, interactive_goal_achieved))
            history_item["score"]["score"] = (
                calculate_reorientation_score(
                    corner_visit_order, interactive_goal_achieved))
        else:
            history_item["score"]["score"] = interactive_goal_achieved
            history_item["score"]["goal_achieved"] = interactive_goal_achieved
        history_item["score"]["reward"] = interactive_reward
        history_item["score"]["ground_truth"] = 1
    elif "score" in history_item:
        history_item["score"]["ground_truth"] = (
            1
            if scene["goal"]["answer"]["choice"] in ["plausible", "expected"]
            else 0
        )

        try:
            classification = float(history_item["score"].get("classification"))
        except (ValueError, TypeError):
            classification = float(-1)
        history_item["score"]["score"] = 1 if \
            classification == float(history_item["score"]["ground_truth"]) else \
            (-1 if classification == -1 else 0)
    else:
            # Eval 2 backwards compatiblity
        history_item["score"] = {'score': -1}
        history_item["score"]["ground_truth"] = 1 if scene[
                "answer"]["choice"] == "plausible" else 0

    # Psychologists wanted to see a definitive answer of correctness
    if history_item["score"]["score"] == 1:
        history_item["score"]["score_description"] = "Correct"
    elif history_item["score"]["score"] == 0:
        history_item["score"]["score_description"] = "Incorrect"
    elif history_item["score"]["score"] == -1:
        history_item["score"]["score_description"] = "No answer"
        history_item["score"]["score"] = 0

    # Calculate Cube Weighted Scoring
    (
        weighted_score,
        weighted_score_worth,
        weighted_confidence
    ) = add_weighted_cube_scoring(history_item, scene)

    history_item["score"]["weighted_score"] = weighted_score
    history_item["score"]["weighted_score_worth"] = weighted_score_worth
    history_item["score"]["weighted_confidence"] = weighted_confidence

    # Agency Scoring Check
    # Get Paired Agency Task
    if history_item["test_type"] == "agents":
        paired_history_item = return_agency_paired_history_item(
            client, db_string, history_item)
        # Only attempt pair scoring if the other pair item has already 
        #   been ingested
        if paired_history_item:
            # Determine which pair item is correct (1), the correct pair
            #   item should have a higher classification to be correct
            if paired_history_item["score"]["ground_truth"] == 1:
                update_agency_scoring(paired_history_item, history_item)
            else:
                update_agency_scoring(history_item, paired_history_item)

            update_agency_paired_history_item(
                client, db_string, paired_history_item)

    return history_item["score"]


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


def build_history_item(
    history_file: str,
    folder: str,
    client: MongoClient,
    db_string: str
) -> dict:
    logging.info(f"Ingest history file: {history_file}")
    mongoDB = client[db_string]

    # Create History Object and add basic information
    history = load_json_file(folder, history_file)

    history_item = {
        'eval': determine_evaluation_hist_name(
            history["info"]["evaluation_name"]
        )
    }

    history_item["evalNumber"] = int(re.sub("[^0-9]", "", history_item["eval"]))
    history_item["performer"] = determine_team_mapping_name(
        history["info"]["team"])
    history_item["name"] = history["info"]["name"]
    history_item["metadata"] = history["info"]["metadata"]
    history_item["fullFilename"] = os.path.splitext(history_file)[0]
    history_item["fileTimestamp"] = history["info"]["timestamp"]
    history_item["score"] = history["score"]

    # Load Scene from Database
    scene_rec_name = determine_evaluation_scene_name(
        history["info"]["evaluation_name"]
    )
    collection_name = get_scene_collection(db_string, client, scene_rec_name)
    collection = mongoDB[collection_name]
    scene = collection.find_one(
        {"name": history_item["name"], "eval": scene_rec_name})

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
    # To get target_is_visible_at_start we need to get it off of step[1],
    #   so there needs to be at least two items in the step array
    if len(history_item["steps"]) > 2:
        if "target_is_visible_at_start" in history_item["steps"][1]:
            history_item["target_is_visible_at_start"] = (
                history_item["steps"][1]["target_is_visible_at_start"]
            )

    if scene:
        # Add some basic scene information into history object to make
        #    UI load times faster then having to query scene every time
        history_item["scene_num"] = scene["scene_num"]
        history_item["test_num"] = scene["test_num"]

        history_item["scene_goal_id"] = scene["goal"]["sceneInfo"]["id"][0]
        if "slices" in scene["goal"]["sceneInfo"]:
            history_item["slices"] = scene["goal"]["sceneInfo"]["slices"]
        else:
            history_item["slices"] = None 
        history_item["test_type"] = scene["goal"]["sceneInfo"]["secondaryType"]
        history_item["category"] = scene["goal"]["sceneInfo"]["primaryType"]

        history_item["hasNovelty"] = scene[
            "goal"]["sceneInfo"]["untrained"]["any"]
        history_item["category_type"] = scene[
            "goal"]["sceneInfo"]["tertiaryType"]

        history_item["score"] = process_score(
            history_item,
            scene,
            interactive_goal_achieved,
            interactive_reward,
            corner_visit_order,
            reorientation_scoring_override,
            client,
            db_string)
        history_item["score"]["scorecard"] = (
            calc_scorecard(history, scene)
            if history_item['category'] == 'interactive' else None
        )

        return history_item


def check_agent_to_corner_position(
        position: dict,
        incorrect_corners: List[dict],
        correct_corners: List[dict],
        corner_visit_order: List[dict]) -> List[dict]:

    corner_visited = None

    # Check if agent is close to any corner
    for corner in REORIENTATION_CORNERS:
        if math.dist(
                [position["x"], position["z"]],
                [
                    REORIENTATION_CORNERS[corner]["x"],
                    REORIENTATION_CORNERS[corner]["z"]
                ]) < DISTANCE_FROM_CORNER:
            corner_visited = corner

    # Return if not near a corner, or still near last corner
    if (
        corner_visited is None
        or corner_visit_order
        and corner_visit_order[-1]["name"] == corner_visited
    ):
        return corner_visit_order

    if corner_visited in incorrect_corners:
        corner_visit_order.append({
            "name": corner_visited,
            "type": "incorrect"
        })

    if corner_visited in correct_corners:
        # Corners get added to correct list, first is always correct
        #   Second corner is always ambiguous corner
        corner_type = "correct" if (
            corner_visited == correct_corners[0]) else ("neutral")
        corner_visit_order.append({
            "name": corner_visited,
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
    new_step = {
        'stepNumber': step["step"],
        'action': step["action"],
        'args': step["args"],
        'classification': step["classification"],
        'confidence': step["confidence"],
        'internal_state': step["internal_state"],
    }

    # TODO: Added if check because key error in 3.75 and earlier
    if "delta_time_millis" in step:
        new_step["delta_time_millis"] = step["delta_time_millis"]
    
    if "target_is_visible_at_start" in step:
        new_step["target_is_visible_at_start"] = step["target_is_visible_at_start"]

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
        if interactive_reward >= 0 - ((number_steps - 1) * 0.001) + 1:
            interactive_goal_achieved = 1

        if "target_visible" in step:
            new_step["target_visible"] = step["target_visible"]

        target_keys = ['target', 'target_1', 'target_2']

        for target in target_keys:
            if target in step["output"]["goal"]["metadata"]:
                output[target] = step["output"]["goal"]["metadata"][target]

    new_step["output"] = output

    return (
        new_step,
        interactive_reward,
        interactive_goal_achieved,
        corner_visit_order)


def calculate_weighted_confidence(history_item: dict, multiplier: int) -> Union[float,None]:
    confidence = history_item["score"].get("confidence")
    if confidence == "None" or confidence is None:
        return None
    else:
        return float(confidence) * multiplier


def add_weighted_cube_scoring(history_item: dict, scene: dict) -> tuple:
    if "goal" in scene and "sceneInfo" in scene["goal"]:
        if scene["goal"]["sceneInfo"]["tertiaryType"] == "shape constancy":
            if history_item["scene_goal_id"] in SHAPE_CONSTANCY_DUPLICATE_CUBE:
                return (history_item["score"]["score"] * 2, 2, calculate_weighted_confidence(history_item, 2))
            elif history_item["scene_goal_id"] in SHAPE_CONSTANCY_8X_CUBE:
                return (history_item["score"]["score"] * 8, 8, calculate_weighted_confidence(history_item, 8))
        elif scene["goal"]["sceneInfo"]["tertiaryType"] == "object permanence":
            if history_item["scene_goal_id"] in PASSIVE_OBJ_PERM_DUPLICATE_CUBE:
                return (history_item["score"]["score"] * 2, 2, calculate_weighted_confidence(history_item, 2))
        elif scene["goal"]["sceneInfo"]["tertiaryType"] in PASSING_CELLS.keys():
            if history_item["scene_goal_id"] not in PASSING_CELLS[scene["goal"]["sceneInfo"]["tertiaryType"]]:
                return (0,0,0)
        return (history_item["score"]["score"], 1, calculate_weighted_confidence(history_item, 1))
    return (0,0,0)

  
def automated_history_ingest_file(
        history_file: str,
        folder: str,
        db_string: str,
        client: MongoClient) -> None:
    mongoDB = client[db_string]

    history_item = build_history_item(
        history_file, folder, client, db_string)
    collection_name = get_history_collection(db_string, client, history_item["eval"])

    collection = mongoDB[collection_name]
    check_exists = collection.find(
        {
            "name": history_item["name"],
            "eval": history_item["eval"],
            "performer": history_item["performer"],
            "metadata": history_item["metadata"]
        }
    )

    matched_files = list(check_exists)

    if len(matched_files) == 0:
        logging.info(f"Inserting {history_item['name']}")
        collection.insert_one(history_item)
    else:
        for item in matched_files:
            if history_item["fileTimestamp"] > item["fileTimestamp"]:
                logging.info(f"Updating {history_item['name']}")
                collection.replace_one({"_id": item["_id"]}, history_item)

    # Add Keys when a list of keys doesn't exist
    if create_collection_keys.check_collection_has_key(
            history_item["eval"], mongoDB) is None:
        create_collection_keys.find_collection_keys(
            collection_name, history_item["eval"], mongoDB)


def calc_scorecard(history_item: dict, scene: dict) -> dict:
    scorecard = Scorecard(history_item, scene)
    return scorecard.score_all()


def calculate_reorientation_true_score(
        corner_visit_order: List[dict],
        interactive_goal_achieved: int) -> int:
    # This is correct if the agent goes to the correct corner first
    if corner_visit_order:
        return 1 if corner_visit_order[0]["type"] == "correct" else 0
    else:
        return interactive_goal_achieved


def calculate_reorientation_score(
        corner_visit_order: List[dict],
        interactive_goal_achieved: int) -> int:
    # This is correct if they get to the correct corner before ever
    #  going to an incorrect corner, so they could go to an
    #  ambiguous/neutral corner first and still be correct
    if len(corner_visit_order) <= 0:
        return interactive_goal_achieved
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


def update_agency_scoring(
        history_item_1: dict,
        history_item_2: dict) -> None:
    # If either classification is none it should be marked as incorrect
    # history_item_1 will always be the correct item when calling this 
    #  so its classification should be higher to be correct
    score_1 = history_item_1["score"]
    score_2 = history_item_2["score"]

    # convert classification field to float
    # if None or unconvertible string, catch exception and assign -1
    try:
        classification_1 = float(score_1.get("classification"))
    except (TypeError, ValueError):
        classification_1 = float(-1)

    try:
        classification_2 = float(score_2.get("classification"))
    except (TypeError, ValueError):
        classification_2 = float(-1)

    if classification_1 == -1 and classification_2 == -1:
        score_1["score"] = 0
        score_1["weighted_score"] = 0
        score_1["weighted_score_worth"] = 1
        score_1["score_description"] = "No answer"

        score_2["score"] = 0
        score_2["weighted_score"] = 0
        score_2["weighted_score_worth"] = 0
        score_2["score_description"] = "No answer"
    elif classification_1 == -1:
        score_1["score"] = 0
        score_1["weighted_score"] = 0
        score_1["weighted_score_worth"] = 0
        score_1["score_description"] = "No answer"

        score_2["score"] = 0
        score_2["weighted_score"] = 0
        score_2["weighted_score_worth"] = 1
        score_2["score_description"] = "Incorrect"
    elif classification_2 == -1:
        score_1["score"] = 0
        score_1["weighted_score"] = 0
        score_1["weighted_score_worth"] = 1
        score_1["score_description"] = "Incorrect"

        score_2["score"] = 0
        score_2["weighted_score"] = 0
        score_2["weighted_score_worth"] = 0
        score_2["score_description"] = "No answer"
    elif classification_1 > classification_2:
        score_1["score"] = 1
        score_1["weighted_score"] = 1
        score_1["weighted_score_worth"] = 1
        score_1["score_description"] = "Correct"

        score_2["score"] = 1
        score_2["weighted_score"] = 1
        score_2["weighted_score_worth"] = 0
        score_2["score_description"] = "Correct"
    else:
        score_1["score"] = 0
        score_1["weighted_score"] = 0
        score_1["weighted_score_worth"] = 1
        score_1["score_description"] = "Incorrect"

        score_2["score"] = 0
        score_2["weighted_score"] = 0
        score_2["weighted_score_worth"] = 0
        score_2["score_description"] = "Incorrect"


def reorientation_calculate_corners(scene: dict) -> List[dict]:
    correct_corners = [scene["goal"]["sceneInfo"]["corner"]]
    if scene["goal"]["sceneInfo"]["ambiguous"]:
        opposite_corner = {k: -v for k, v in REORIENTATION_CORNERS[
            scene["goal"]["sceneInfo"]["corner"]].items()}
        for k, v in REORIENTATION_CORNERS.items():
            if(opposite_corner == v):
                correct_corners.append(k)

    incorrect_corners = [
        k
        for k, v in REORIENTATION_CORNERS.items()
        if (k not in correct_corners)
    ]

    return (incorrect_corners, correct_corners)


