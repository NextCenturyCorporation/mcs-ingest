import mcs_history_ingest

def apply_correct_weighted_scores(mongoDB):
    print("Begin updating weighted scoring for Evaluation  6 Results")

    results_collection = mongoDB["eval_6_results"]
    scenes_collection = mongoDB["eval_6_scenes"]
    history_files = results_collection.find({})

    for history in history_files:
        scene = scenes_collection.find_one({"name": history["name"]})

        (
            weighted_score,
            weighted_score_worth,
            weighted_confidence
        ) = mcs_history_ingest.add_weighted_cube_scoring(history, scene)

        history["score"]["weighted_score"] = weighted_score
        history["score"]["weighted_score_worth"] = weighted_score_worth
        history["score"]["weighted_confidence"] = weighted_confidence

        results_collection.replace_one({"_id": history["_id"]}, history)

    print("Completed updating weighted scoring for Evaluation 6 Results")