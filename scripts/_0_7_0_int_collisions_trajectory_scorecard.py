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

def update_int_collisions_trajectory_scorecard(mongoDB):
    results_collection = mongoDB["eval_6_results"]
    scenes_collection = mongoDB["eval_6_scenes"]

    # Update the Scorecard for Interactive Collisions and Trajectory
    category_types = ["interactive collision", "trajectory"]

    history_files = results_collection.find({
        "category_type": { "$in": category_types}
    })
    for history_record in history_files:
        scene = scenes_collection.find_one({"name": history_record["name"]})
        
        # Download History file (the history record doesn't have everything we need
        # to calculate correct_door_opened)
        bucket = s3.Bucket("evaluation-images")
        history_file = "eval-resources-6/" + history_record["fullFilename"] + ".json"
        basename = history_record["fullFilename"] + ".json"
        print(f"Downloading {basename}")
        bucket.download_file(history_file, basename)

        history_item = load_json_file(basename)
        scorecard = Scorecard(history_item, scene)
        scorecard.calc_correct_platform_side()
        scorecard.calc_correct_door_opened()

        history_record["score"]["scorecard"]["correct_platform_side"] = scorecard.get_correct_platform_side()
        history_record["score"]["scorecard"]["correct_door_opened"] = scorecard.get_correct_door_opened()
        results_collection.replace_one({"_id": history_record["_id"]}, history_record)
        os.remove(basename)

    print("Updated Interactive Collision and Trajectory Scorecard correct platform side and correct door opened")

