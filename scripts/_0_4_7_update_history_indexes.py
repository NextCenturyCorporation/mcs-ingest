def create_new_cat_eval2_and_indexes(mongoDB):
    collection = mongoDB["mcs_history"]

    result = collection.update_many(
        {
            "eval": "Evaluation 2 Results",
            "test_type": "intuitive physics"
        }, [{
            "$set": {
                'cat_type_pair': '$category_type'
            }
        }])

    print("Updated Eval 2 Intuitive Physics Results Data:  " + str(
        result.matched_count))

    result = collection.update_many(
        {
            "eval": "Evaluation 2 Results",
            "test_type": "interactive"
        }, [{
            "$set": {
                'cat_type_pair': {"$concat" : ['$category_pair', '_', '$category_type']}
            }
        }])

    print("Updated Eval 2 Interactive Results Data:  " + str(
        result.matched_count))

    result = collection.create_index([
        ("metadata", 1)
    ])

    print("Index creation result: ", result)

    result = collection.create_index([
        ("test_num", 1)
    ])

    print("Index creation result: ", result)

    result = collection.create_index([
        ("cat_type_pair", 1)
    ])

    print("Index creation result: ", result)
