import argparse
import io
import json
import logging
import math
import os
import re

from typing import List

from pymongo import MongoClient
import create_collection_keys

from scorecard import Scorecard


HISTORY_INDEX = "mcs_history"
SCENE_INDEX = "mcs_scenes"
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
        eval_name: str, history_eval_name: str) -> str:
    eval_str = ""
    if eval_name is None:
        return (
            EVAL_HIST_MAPPING_DICT[history_eval_name]
            if history_eval_name in EVAL_HIST_MAPPING_DICT
            else history_eval_name
        )

    else:
        return eval_name


def return_agency_paired_history_item(
        client: MongoClient,
        db_string: str,
        history_item: dict) -> dict:
    mongoDB = client[db_string]
    collection = mongoDB[HISTORY_INDEX]
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
    collection = mongoDB[HISTORY_INDEX]
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


def ingest_to_mongo(index: str, ingest_files: dict, client: MongoClient):
    mongoDB = client['mcs']
    collection = mongoDB[index]
    result = collection.insert_many(ingest_files)
    logging.info(f"Inserted {len(result.inserted_ids)} out of " +
                 f"{len(ingest_files)}. Result: {result}")


def build_history_item(
    history_file: str,
    folder: str,
    eval_name: str,
    performer: str,
    scene_folder: str,
    extension: str,
    client: MongoClient,
    db_string: str
) -> dict:
    logging.info(f"Ingest history file: {history_file}")
    mongoDB = client[db_string]

    # Create History Object and add basic information
    history = load_json_file(folder, history_file)

    history_item = {
        'eval': determine_evaluation_hist_name(
            eval_name, history["info"]["evaluation_name"]
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

        # Add Keys when a list of keys doesn't exist
        if create_collection_keys.check_collection_has_key(
                scene["eval"], mongoDB) is None:
            print("Add Scene Keys")
            create_collection_keys.find_collection_keys(
                SCENE_INDEX, scene["eval"], mongoDB)

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
    new_step["output"] = output

    return (
        new_step,
        interactive_reward,
        interactive_goal_achieved,
        corner_visit_order)


def add_weighted_cube_scoring(history_item: dict, scene: dict) -> tuple:
    weighted_score, weighted_score_worth, weighted_confidence = 0, 0, 0
    if "goal" in scene and "sceneInfo" in scene["goal"]:
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

  
def automated_history_ingest_file(
        history_file: str,
        folder: str,
        db_string: str,
        client: MongoClient) -> None:
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

    # Add Keys when a list of keys doesn't exist
    if create_collection_keys.check_collection_has_key(
            history_item["eval"], mongoDB) is None:
        create_collection_keys.find_collection_keys(
            HISTORY_INDEX, history_item["eval"], mongoDB)


def find_history_files(folder: str, extension: str) -> dict:
    history_files = [
        f for f in os.listdir(
            folder) if str(f).endswith("." + extension)]
    history_files.sort()
    return history_files


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
            if (
                item["fullFilename"] == history_item["fullFilename"]
                and history_item["fileTimestamp"] > item["fileTimestamp"]
            ):
                replacementIndex = index

        if replacementIndex == -1:
            ingest_history.append(history_item)
        else:
            ingest_history[replacementIndex] = history_item

    ingest_to_mongo(HISTORY_INDEX, ingest_history, client)

    create_collection_keys.find_collection_keys(
        HISTORY_INDEX, eval_name, mongoDB)


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


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Ingest MCS History JSON files into Elasticsearch')
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
        '--extension',
        required=False,
        default="json",
        help='History file extension for legacy ingest')

    args = parser.parse_args()

    ingest_history_files(
        args.folder,
        args.eval_name,
        args.performer,
        args.scene_folder,
        args.extension
    )


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()
