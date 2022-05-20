def add_slice_to_history_items(mongoDB):
    # Eval 2 did not have a hypercube design so no slices
    collection_numbers = ["3", "3_5", "3_75", "4"]

    for eval_number in collection_numbers:
        results_collection = mongoDB["eval_" + eval_number + "_results"]
        scenes_collection = mongoDB["eval_" + eval_number + "_scenes"]

        history_files = results_collection.find({})

        for history in history_files:
            scene = scenes_collection.find_one({"name": history["name"]})
            if "slices" in scene["goal"]["sceneInfo"]:
                history["slices"] = scene["goal"]["sceneInfo"]["slices"]
                results_collection.replace_one({"_id": history["_id"]}, history)

        print("Updated slices for Eval " + str(eval_number) + ".")
