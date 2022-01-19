def copy_indexes(mongoDB, old_collection, new_collection_name):
    new_scenes_collection = mongoDB[new_collection_name]
    scene_indexes = old_collection.index_information()
    for key in scene_indexes:
        index_tuple = scene_indexes[key]["key"][0]
        new_scenes_collection.create_index([(index_tuple[0], int(index_tuple[1]))])

    print("Copied all indexes to: " + str(new_collection_name))


def create_new_collection(collection, eval_name, collection_name, eval_number):
    pipeline = [
        {
            "$match": {"eval": eval_name}
        }, {
            "$out": collection_name
        }
    ]

    results = collection.aggregate(pipeline)

    print("Create new Eval " + str(eval_number) + " Scenes Collection.", results)


def mapping_insert(mapping_collection, eval_name, collection_name):
    mapping_collection.insert_one({"name": eval_name, "collection": collection_name})
    print("Added new mapping for: " + str(eval_name))


def migrate_collections(mongoDB):
    history_collection = mongoDB["mcs_history"]
    scenes_collection = mongoDB["mcs_scenes"]

    scene_mapping = mongoDB["scenes_mapping"]
    history_mapping = mongoDB["history_mapping"]

    evalNumbers = [2, 3, 3.5, 3.75, 4]

    for en in evalNumbers:
        # Handle logic for copying Scenes
        eval_scenes_pretty_name = "Evaluation " + str(en) + " Scenes"
        eval_scenes_collection_name = "eval_" + (str(en)).replace(".", "_") + "_scenes"

        mapping_insert(scene_mapping, eval_scenes_pretty_name, eval_scenes_collection_name)
        create_new_collection(scenes_collection, eval_scenes_pretty_name, eval_scenes_collection_name, en)
        copy_indexes(mongoDB, scenes_collection, eval_scenes_collection_name)

        # Handle logic for copying History
        eval_history_pretty_name = "Evaluation " + str(en) + " Results"
        eval_history_collection_name = "eval_" + (str(en)).replace(".", "_") + "_results"

        mapping_insert(history_mapping, eval_history_pretty_name, eval_history_collection_name)
        create_new_collection(history_collection, eval_history_pretty_name, eval_history_collection_name, en)
        copy_indexes(mongoDB, history_collection, eval_history_collection_name)

    # Remove old collections after new collections set up
    history_collection.drop()
    scenes_collection.drop()
