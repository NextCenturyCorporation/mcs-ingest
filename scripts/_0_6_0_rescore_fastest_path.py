from scorecard import Scorecard
import boto3
import os
import json
import io

s3 = boto3.resource('s3')

def load_json_file(file_name: str) -> dict:
    with io.open(
            file_name,
            mode='r',
            encoding='utf-8-sig') as json_file:
        return json.loads(json_file.read())

def update_fastest_path(mongoDB):
    store_path_properties(mongoDB)
    rescore_fastest_path(mongoDB)

def store_path_properties(mongoDB):
    scenes_collection = mongoDB["eval_5_scenes"]

    category_types = ["lava", "holes"]

    scene_files = scenes_collection.find({
        "goal.sceneInfo.tertiaryType": { "$in": category_types}
    })

    for scene_record in scene_files:
        #Download Scene file
        goal_id = scene_record["goal"]["sceneInfo"]["id"][0]
        scene_debug_name = scene_record["name"] + "_" + goal_id + "_debug"
        bucket = s3.Bucket("evaluation-images")
        scene_file = "eval-scenes-5/" + scene_debug_name + ".json"
        scene_basename = scene_debug_name + ".json"
        print(f"Downloading scene file {scene_basename}")
        bucket.download_file(scene_file, scene_basename)

        scene_item = load_json_file(scene_basename)
        scene_record["path"] = scene_item["debug"]["path"]
        scene_record["slowPath"] = scene_item["debug"]["slowPath"]
        scenes_collection.replace_one({"_id": scene_record["_id"]}, scene_record)
        os.remove(scene_basename)

    print("Updated holes and lava scenes with path and slowPath")

def rescore_fastest_path(mongoDB):
    results_collection = mongoDB["eval_5_results"]
    scenes_collection = mongoDB["eval_5_scenes"]

    category_types = ["lava", "holes"]
    history_files = results_collection.find({ "category_type": { "$in": category_types}})

    for history_record in history_files:
        scene = scenes_collection.find_one({"name": history_record["name"]})

        #Download History file
        bucket = s3.Bucket("evaluation-images")
        history_file = "eval-resources-5/" + history_record["fullFilename"] + ".json"
        hist_basename = history_record["fullFilename"] + ".json"
        print(f"Downloading history file {hist_basename}")
        bucket.download_file(history_file, hist_basename)

        history_item = load_json_file(hist_basename)
        scorecard = Scorecard(history_item, scene)
        scorecard.calc_fastest_path()

        history_record["score"]["scorecard"]["fastest_path"] = scorecard.is_fastest_path
        results_collection.replace_one({"_id": history_record["_id"]}, history_record)
        os.remove(hist_basename)


    print("Updated scorecard for fastest path.")
