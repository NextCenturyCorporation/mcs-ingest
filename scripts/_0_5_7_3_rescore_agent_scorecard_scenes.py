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


def rescore_interacted_with_agent(mongoDB):
    results_collection = mongoDB["eval_5_results"]
    scenes_collection = mongoDB["eval_5_scenes"]

    history_files = results_collection.find({"category": "interactive"})

    for history_record in history_files:
        scene = scenes_collection.find_one({"name": history_record["name"]})

        #Download History file
        bucket = s3.Bucket("evaluation-images")
        history_file = "eval-resources-5/" + history_record["fullFilename"] + ".json"
        basename = history_record["fullFilename"] + ".json"
        print(f"Downloading {basename}")
        bucket.download_file(history_file, basename)

        history_item = load_json_file(basename)
        scorecard = Scorecard(history_item, scene)
        scorecard.calc_agent_interactions()

        history_record["score"]["scorecard"]["interact_with_agent"] = scorecard.get_interact_with_agent()
        results_collection.replace_one({"_id": history_record["_id"]}, history_record)
        os.remove(basename)


    print("Updated scorecard for successful agent interactions.")
