from pymongo import MongoClient

client = MongoClient(
    'mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
mongoDB = client['mcs']


def drop_collections():
    mongoDB["mcs_history_keys"].drop()
    mongoDB["mcs_scenes_keys"].drop()
    print("Collections were successfully removed!")
