def update_test_types(mongoDB):
    collection = mongoDB["mcs_history"]

    result = collection.update_many(
        {
            "eval": "Evaluation 2 Results",
            "test_type": {"$regex": "pair", "$options": 'i'}
        }, {
            "$set": {'test_type': 'interactive'}
        })

    print("Updated to Eval 2 Interactive Test Type:  " + str(
        result.matched_count))

    result = collection.update_many(
        {
            "eval": "Evaluation 2 Results",
            "test_type": {"$ne": "interactive"}
        }, [{
            "$set": {
                'test_type': 'intuitive physics',
                'score.weighted_score': '$score.score',
                'score.weighted_score_worth': 1
            }
        }])

    print("Updated to Eval 2 Intutitive Physics Test Type:  " + str(
        result.matched_count))

    result = collection.create_index([
        ("eval", 1), ("test_type", 1)
    ])

    print("Index creation result: ", result)

    result = collection.create_index([
        ("eval", 1), ("test_type", 1), ("metadata", 1)
    ])

    print("Index creation result: ", result)
