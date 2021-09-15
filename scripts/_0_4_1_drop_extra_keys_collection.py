import logging

def drop_collections(mongoDB):
    mongoDB["mcs_history_keys"].drop()
    mongoDB["mcs_scenes_keys"].drop()
    logging.info("Collections were successfully removed!")
