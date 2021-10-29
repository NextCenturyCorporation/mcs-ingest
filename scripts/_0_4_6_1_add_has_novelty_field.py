def add_has_novelty_field(mongoDB):
    history_collection = mongoDB["mcs_history"]
    scenes_collection = mongoDB["mcs_scenes"]

    result = history_collection.update_many(
        {
            "eval": {"$ne": "Evaluation 3 Results"}
        }, [{
            "$set": {
                'hasNovelty': False
            }
        }])

    print("All non Eval 3 files updated to no novelty.", result)

    history_files = history_collection.find({"eval": "Evaluation 3 Results"})

    for history in history_files:
        scene = scenes_collection.find_one({
            "name": history["name"], "eval": "Evaluation 3 Scenes"})
        history["hasNovelty"] = scene["goal"]["sceneInfo"]["untrained"]["any"]
        history_collection.replace_one({"_id": history["_id"]}, history)

    print("Updated Eval 3 history to appropriate novelty level.")
