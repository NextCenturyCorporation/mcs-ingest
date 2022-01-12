def migrate_collections(mongoDB):
    history_collection = mongoDB["mcs_history"]
    scenes_collection = mongoDB["mcs_scenes"]

    scene_mapping = mongoDB["scenes_mapping"]
    history_mapping = mongoDB["history_mapping"]

    evalNumbers = [2, 3, 3.5, 3.75, 4]

    for en in evalNumbers:
        eval_scenes_pretty_name = "Evaluation " + str(en) + " Scenes"
        eval_scenes_collection_name = "eval_" + (str(en)).replace(".", "_") + "_scenes"

        scene_mapping.insert_one({"name": eval_scenes_pretty_name, "collection": eval_scenes_collection_name})

        scene_pipeline = [
            {
                "$match": {"eval": eval_scenes_pretty_name}
            }, {
                "$out": eval_scenes_collection_name
            }
        ]

        scene_results = scenes_collection.aggregate(scene_pipeline)

        print("Create new Eval " + str(en) + " Scenes Collection.", scene_results)

        new_scenes_collection = mongoDB[eval_scenes_collection_name]
        scene_indexes = scenes_collection.index_information()
        for key in scene_indexes:
            index_tuple = scene_indexes[key]["key"][0]
            new_scenes_collection.create_index([(index_tuple[0], int(index_tuple[1]))])

        print("Copied all indexes to new Scenes Collection.")

        eval_history_pretty_name = "Evaluation " + str(en) + " Results"
        eval_history_collection_name = "eval_" + (str(en)).replace(".", "_") + "_results"

        history_mapping.insert_one({"name": eval_history_pretty_name, "collection": eval_history_collection_name})

        scene_pipeline = [
            {
                "$match": {"eval": eval_history_pretty_name}
            }, {
                "$out": eval_history_collection_name
            }
        ]

        history_results = history_collection.aggregate(scene_pipeline)

        print("Create new Eval " + str(en) + " Results Collection.", history_results)

        new_results_collection = mongoDB[eval_history_collection_name]
        history_indexes = history_collection.index_information()
        for key in history_indexes:
            index_tuple = history_indexes[key]["key"][0]
            new_results_collection.create_index([(index_tuple[0], int(index_tuple[1]))])

        print("Copied all indexes to new Results Collection.")

    history_collection.drop()
    scenes_collection.drop()

    