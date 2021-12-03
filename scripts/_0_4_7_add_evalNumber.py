def add_eval_number(mongoDB):
    history_collection = mongoDB["mcs_history"]
    scenes_collection = mongoDB["mcs_scenes"]

    evalNumbers = [2, 3, 3.5, 3.75, 4]

    for en in evalNumbers:
        result = history_collection.update_many(
            {
                "eval": "Evaluation " + str(en) + " Results"
            }, [{
                "$set": {
                    'evalNumber': en
                }
            }])

        print("Update Eval " + str(en) + " Results.", result)

        result = scenes_collection.update_many(
            {
                "eval": "Evaluation " + str(en) + " Scenes"
            }, [{
                "$set": {
                    'evalNumber': en
                }
            }])

        print("Update Eval " + str(en) + " Scenes.", result)
