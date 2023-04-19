import mcs_history_ingest

def correct_shape_constancy_weights(mongoDB):
    results_collection = mongoDB["eval_6_results"]
    scenes_collection = mongoDB["eval_6_scenes"]

    # This will only get NYU agent tasks, "seeing leads to knowing" has
    #   a test_type of "passive" 
    history_files = results_collection.find({"category_type": "shape constancy"})

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