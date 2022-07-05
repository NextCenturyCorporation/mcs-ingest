def update_scorecard_fields(mongoDB):
    results_collection = mongoDB["eval_4_results"]

    result = results_collection.update_many(
    {
        "score.scorecard.multiple_container_look": {"$exists": True}
    }, {
        "$rename": {'score.scorecard.multiple_container_look': 'score.scorecard.container_relook'}
    }, False)

    print("update_many performed on " + str(
        result.matched_count) + " documents")

    # need to rename temporarily first to avoid "The source and target 
    # field for $rename must not be on the same path" error
    result = results_collection.update_many(
    {
        "score.scorecard.repeat_failed": {"$exists": True}
    }, {
        "$rename": {'score.scorecard.repeat_failed': 'temp_repeat'}
    }, False)

    result = results_collection.update_many(
    {
        "temp_repeat": {"$exists": True}
    }, {
        "$rename": {'temp_repeat': 'score.scorecard.repeat_failed.total_repeat_failed'}
    }, False)

    # need to rename temporarily first to avoid "The source and target 
    # field for $rename must not be on the same path" error
    result = results_collection.update_many(
    {
        "score.scorecard.repeat_failed": {"$exists": True}
    }, {
        "$rename": {'score.scorecard.open_unopenable': 'temp_unopen'}
    }, False)

    result = results_collection.update_many(
    {
        "temp_unopen": {"$exists": True}
    }, {
        "$rename": {'temp_unopen': 'score.scorecard.open_unopenable.total_unopenable_attempts'}
    }, False)


    print("update_many performed on " + str(
        result.matched_count) + " documents")


    print("Updated scorecard fields from Eval 4.")
