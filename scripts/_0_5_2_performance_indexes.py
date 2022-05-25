def create_new_performance_indexes(mongoDB):
    collection_numbers = ["2", "3_5", "3_75", "4"]

    for eval_number in collection_numbers:
        results_collection = mongoDB["eval_" + eval_number + "_results"]
        result = results_collection.create_index([
            ("test_type", 1), ("category", 1)
        ])

        print("Index creation result: ", result)

        result = results_collection.create_index([
            ("test_type", 1), ("metadata", 1)
        ])

        print("Index creation result: ", result)

        scenes_collection = mongoDB["eval_" + eval_number + "_scenes"]

        result = results_collection.create_index([
            ("test_type", 1), ("metadata", 1)
        ])

        print("Index creation result: ", result)