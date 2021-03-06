import json
import os
import sys
import argparse
import io

from collections.abc import MutableMapping
from pymongo import MongoClient

# We might want to move mongo user/pass to new file
client = MongoClient(
    'mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
mongoDB = client['mcs']

# Currently just removing image mag from scene files, might
#    wish to move more keys, or remove so much from the schema
#    that we want to just map the fields we want to the schema
KEYS_TO_DELETE = [
    'image',
    'sequenceNumber',
    'hypercubeNumber',
    'sceneNumber'
]

SCENE_INDEX = "mcs_scenes"
HISTORY_INDEX = "mcs_history"

# Convert names used in config to 'pretty' names for UI
TEAM_MAPPING_DICT = {
    "mess": "MESS-UCBerkeley",
    "mit": "IBM-MIT-Harvard-Stanford",
    "opics": "OPICS (OSU, UU, NYU)",
    "baseline": "TA2 Baseline"
}

# Convert Eval names used to 'pretty' names for UI
EVAL_MAPPING_DICT = {
    "eval_3-5": "Evaluation 3.5 Results",
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
SCENE_DEBUG_EXTENSION = "_debug.json"


def load_json_file(folder: str, file_name: str) -> dict:
    with io.open(
            os.path.join(
                folder, file_name),
            mode='r',
            encoding='utf-8-sig') as json_file:
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


def ingest_to_mongo(index: str, ingest_files: dict):
    collection = mongoDB[index]
    result = collection.insert_many(ingest_files)
    print("Inserted {0} out of {1}.  Result: {2}".format(
        len(result.inserted_ids), len(ingest_files), result))


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
    print("Ingest scene file: {}".format(file_name))
    scene = load_json_file(folder, file_name)

    if eval_name is None:
        scene["eval"] = scene["evaluation"]
        eval_name = scene["evaluation"]
    else:
        scene["eval"] = eval_name

    scene["scene_num"] = scene["sceneNumber"]
    if "sequenceNumber" in scene:
        scene["test_num"] = scene["sequenceNumber"]
    else:
        scene["test_num"] = scene["hypercubeNumber"]

    if "sequenceId" in scene["goal"]["sceneInfo"]:
        scene["goal"]["sceneInfo"]["hypercubeId"] = scene["goal"][
            "sceneInfo"]["sequenceId"]
        del scene["goal"]["sceneInfo"]["sequenceId"]

    scene = delete_keys_from_scene(scene, KEYS_TO_DELETE)

    return scene


def automated_scene_ingest_file(file_name: str, folder: str) -> None:
    # Called from mcs_automated_ingest when a new message in pulled
    #    from the AWS Queue, singular scene file
    scene_item = build_scene_item(file_name, folder, None)
    collection = mongoDB[SCENE_INDEX]
    check_exists = collection.find(
        {
            "name": scene_item["name"],
            "evaluation": scene_item["evaluation"]
        }
    )

    # Do not insert a scene if we already have it in the database
    #     for this particular evaluation
    if check_exists.count() == 0:
        print(f"Inserting {scene_item['name']}")
        collection.insert_one(scene_item)


def ingest_scene_files(folder: str, eval_name: str) -> None:
    # Legacy way of adding scene files from a folder, leaving code
    #   in case automated ingestion has issues in future, bulk ingest
    scene_files = find_scene_files(folder)
    ingest_scenes = []

    for file in scene_files:
        scene = build_scene_item(file, folder, eval_name)
        ingest_scenes.append(scene)

    ingest_to_mongo(SCENE_INDEX, ingest_scenes)


def determine_evaluation_name(eval_name: str, history_eval_name: str) -> str:
    eval_str = ""
    if eval_name is None:
        if history_eval_name in EVAL_MAPPING_DICT:
            eval_str = EVAL_MAPPING_DICT[history_eval_name]
        else:
            eval_str = history_eval_name
    else:
        eval_str = eval_name
    return eval_str


def determine_team_mapping_name(info_team: str) -> str:
    name_str = ""
    if info_team in TEAM_MAPPING_DICT:
        name_str = TEAM_MAPPING_DICT[info_team]
    else:
        name_str = info_team
    return name_str


def build_new_step_obj(
        step: dict,
        interactive_reward: int,
        interactive_goal_achieved: int,
        number_steps: int) -> tuple:
    new_step = {}
    new_step["stepNumber"] = step["step"]
    new_step["action"] = step["action"]
    new_step["args"] = step["args"]
    new_step["classification"] = step["classification"]
    new_step["confidence"] = step["confidence"]
    new_step["internal_state"] = step["internal_state"]

    # If too many items in violations_xy_list, take the first 50
    if(step["violations_xy_list"] and isinstance(
        step["violations_xy_list"], list) and len(
            step["violations_xy_list"]) > MAX_XY_VIOLATIONS):
        new_step["violations_xy_list"] = step[
            "violations_xy_list"][:MAX_XY_VIOLATIONS]
    else:
        new_step["violations_xy_list"] = step["violations_xy_list"]

    output = {}
    if("output" in step):
        output["return_status"] = step["output"]["return_status"]
        output["reward"] = step["output"]["reward"]
        output["physics_frames_per_second"] = step[
            "output"]["physics_frames_per_second"]
        interactive_reward = output["reward"]
        if(output["reward"] >= (0 - ((number_steps - 1) * 0.001) + 1)):
            interactive_goal_achieved = 1
    new_step["output"] = output

    return (new_step, interactive_reward, interactive_goal_achieved)


def add_weighted_cube_scoring(history_item: dict, scene: dict) -> tuple:
    weighted_score, weighted_score_worth, weighted_confidence = 0, 0, 0
    if "goal" in scene:
        if "sceneInfo" in scene["goal"]:
            if scene["goal"]["sceneInfo"]["tertiaryType"] == "shape constancy":
                if history_item[
                        "scene_goal_id"] in SHAPE_CONSTANCY_DUPLICATE_CUBE:
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


def process_score(
        history_item: dict,
        scene: dict,
        interactive_goal_achieved: int,
        interactive_reward: int) -> dict:
    # Removed Adjusted Confidence, should be OBE
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
            history_item["score"]["score"] = 1 if history_item["score"][
                "classification"] == scene["goal"]["answer"]["choice"] else 0
            history_item["score"]["ground_truth"] = 1 if ("plausible" == scene[
                "goal"]["answer"]["choice"] or "expected" == scene[
                    "goal"]["answer"]["choice"]) else 0
        else:
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


def build_history_item(
        history_file: str,
        folder: str,
        eval_name: str,
        performer: str,
        scene_folder: str,
        extension: str) -> dict:
    print("Ingest history file: {}".format(history_file))
    # Create History Object and add basic information
    history = {}
    history = load_json_file(folder, history_file)

    history_item = {}
    history_item["eval"] = determine_evaluation_name(
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
            interactive_goal_achieved
        ) = build_new_step_obj(
            step,
            interactive_reward,
            interactive_goal_achieved,
            number_steps)
        steps.append(new_step)

    history_item["steps"] = steps
    history_item["step_counter"] = number_steps

    # Load Scene from Database or File
    scene = None
    if scene_folder is None:
        collection = mongoDB[SCENE_INDEX]
        scene = collection.find_one({"name": history_item["name"]})
    else:
        scene = load_json_file(
            scene_folder, history_item["name"] + SCENE_DEBUG_EXTENSION)

    if scene:
        # Add some basic scene information into history object to make
        #    UI load times faster then having to query scene every time
        if scene_folder is None:
            history_item["scene_num"] = scene["scene_num"]
            history_item["test_num"] = scene["test_num"]
        else:
            history_item["scene_num"] = scene["sceneNumber"]
            history_item["test_num"] = scene["hypercubeNumber"]

        history_item["scene_goal_id"] = scene["goal"]["sceneInfo"]["id"][0]
        history_item["test_type"] = scene["goal"]["sceneInfo"]["secondaryType"]
        history_item["category"] = scene["goal"]["sceneInfo"]["primaryType"]

        # TODO: Make sure this was fixed so we no longer need to do
        #   check, might need quaternary type
        # MCS-578 https://nextcentury.atlassian.net/jira/software/projects/MCS/boards/94?selectedIssue=MCS-578&text=578 # noqa: E501
        if scene["goal"]["sceneInfo"]["tertiaryType"] == "retrieval":
            history_item["category_type"] = scene[
                "goal"]["sceneInfo"]["name"][:-3]
        else:
            history_item["category_type"] = scene[
                "goal"]["sceneInfo"]["tertiaryType"]

        history_item["score"] = process_score(
            history_item,
            scene,
            interactive_goal_achieved,
            interactive_reward)

    return history_item


def automated_history_ingest_file(history_file: str, folder: str) -> None:
    history_item = build_history_item(
        history_file, folder, None, None, None, "json")
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
        print(f"Inserting {history_item['name']}")
        collection.insert_one(history_item)
    else:
        for item in check_exists:
            if history_item["fileTimestamp"] > item["fileTimestamp"]:
                print(f"Updating {history_item['name']}")
                collection.replace_one({"_id": item["_id"]}, history_item)


def ingest_history_files(
        folder: str,
        eval_name: str,
        performer: str,
        scene_folder: str,
        extension: str) -> None:
    history_files = find_history_files(folder, extension)
    ingest_history = []

    for file in history_files:
        history_item = build_history_item(
            file, folder, eval_name, performer, scene_folder, extension)

        replacementIndex = -1
        for index, item in enumerate(ingest_history):
            if item["fullFilename"] == history_item[
                    "fullFilename"] and history_item[
                    "fileTimestamp"] > item["fileTimestamp"]:
                replacementIndex = index

        if replacementIndex == -1:
            ingest_history.append(history_item)
        else:
            ingest_history[replacementIndex] = history_item

    ingest_to_mongo(HISTORY_INDEX, ingest_history)


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
    main(sys.argv)
