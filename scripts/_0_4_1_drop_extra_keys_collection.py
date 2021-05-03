def drop_collections(mongoDB):
    mongoDB["mcs_history_keys"].drop()
    mongoDB["mcs_scenes_keys"].drop()
    print("Collections were successfully removed!")
