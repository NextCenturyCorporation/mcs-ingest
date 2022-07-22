from scorecard import Scorecard

def rescore_platform_side(mongoDB):
    results_collection = mongoDB["eval_5_results"]
    scenes_collection = mongoDB["eval_5_scenes"]

    history_files = results_collection.find({"category": "interactive"})

    for history in history_files:
        scene = scenes_collection.find_one({"name": history["name"]})
        scorecard = Scorecard(history, scene)

        history["score"]["scorecard"]["correct_platform_side"] = scorecard.calc_correct_platform_side()
        results_collection.replace_one({"_id": history["_id"]}, history)


    print("Updated correct platform side fields.")
