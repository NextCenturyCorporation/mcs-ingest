import logging

from pymongo import MongoClient
from bson.objectid import ObjectId

HISTORY_INDEX = "mcs_history"
SCENE_INDEX = "mcs_scenes"
COLL_KEYS_INDEX = "collection_keys"
EVAL_3_RESULTS = "Evaluation 3 Results"
EVAL_2_RESULTS = "Evaluation 2 Results"
EVAL_3_SCENES = "Evaluation 3 Scenes"
EVAL_2_SCENES = "Evaluation 2 Scenes"

# We might want to move mongo user/pass to new file
client = MongoClient('mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
mongoDB = client['mcs']


def update_scene_num_refs_history_eval_3():
    logging.info("Begin Processing " + EVAL_3_RESULTS)
    collection = mongoDB[HISTORY_INDEX]

    # rename scene_part_num field to test_num
    result = collection.update_many(
        {
            "eval": EVAL_3_RESULTS,
            "scene_part_num": {"$exists": True}
        }, {
            "$rename": {'scene_part_num': 'test_num'}
        }, False)

    logging.info("update_many performed on " + str(
        result.matched_count) + " documents")


def update_scene_num_refs_history_eval_2():
    logging.info("Begin Processing " + EVAL_2_RESULTS)
    collection = mongoDB[HISTORY_INDEX]

    documents = list(collection.find(
        {
            "eval": EVAL_2_RESULTS,
            "scene_num": {"$exists": True},
            "scene_part_num": {"$exists": True}
        }).batch_size(1000))

    logging.info("Found " + str(len(documents)) + " results")

    for doc in documents:

        test_num = int(doc["scene_num"])
        scene = int(doc["scene_part_num"])

        collection.update_one(
            {"_id": ObjectId(doc["_id"])}, [
                {
                    "$set": {'scene_num': scene, 'test_num': test_num}
                }, {
                    "$unset": ['scene_part_num', 'url_string']
                }
            ], True)


def update_scene_num_refs_scenes_eval_2():
    logging.info("Begin Processing " + EVAL_2_SCENES)
    collection = mongoDB[SCENE_INDEX]

    documents = list(collection.find(
        {
            "eval": EVAL_2_SCENES,
            "scene_num": {"$exists": True},
            "scene_part_num": {"$exists": True}
        }).batch_size(1000))

    logging.info("Found " + str(len(documents)) + " results")

    for doc in documents:

        test_num = int(doc["scene_num"])
        scene = int(doc["scene_part_num"])

        collection.update_one(
            {"_id": ObjectId(doc["_id"])}, [
                {
                    "$set": {
                        'scene_num': scene,
                        'test_num': test_num
                    }
                }, {
                    "$unset": ['scene_part_num']
                }
            ], True)


def update_scene_num_refs_scenes_eval_3():
    logging.info("Begin Processing " + EVAL_3_SCENES)
    collection = mongoDB[SCENE_INDEX]

    documents = list(collection.find(
        {
            "eval": EVAL_3_SCENES,
            "sequenceNumber": {"$exists": True},
            "sceneNumber": {"$exists": True},
            "goal.sceneInfo.sequenceId": {"$exists": True}
        }).batch_size(1000))

    logging.info("Found " + str(len(documents)) + " results")

    for doc in documents:
        test_num = doc["sequenceNumber"]
        scene = doc["sceneNumber"]
        hypercubeId = doc["goal"]["sceneInfo"]["sequenceId"]

        collection.update_one(
            {"_id": ObjectId(doc["_id"])},
            [
                {
                    "$set": {
                        'scene_num': scene,
                        'test_num': test_num,
                        "goal.sceneInfo.hypercubeId": hypercubeId
                    }
                },
                {
                    "$unset": [
                        'sequenceNumber',
                        'sceneNumber',
                        'goal.sceneInfo.sequenceId'
                    ]
                }
            ], True)


def update_collection_keys():
    logging.info("Begin Processing collection_keys...")
    collection = mongoDB["collection_keys"]

    documents = list(collection.find({}))
    logging.info("Found " + str(len(documents)) + " results")

    for doc in documents:
        if('scene_part_num' in doc['keys'] and "Results" in doc['name']):
            collection.update_one(
                {"_id": ObjectId(doc["_id"])},
                {"$push": {'keys': "test_num"}},
                True)
            collection.update_one(
                {"_id": ObjectId(doc["_id"])},
                {"$pull": {'keys': "scene_part_num"}},
                True)
        else:
            keys_to_add = []
            keys_to_remove = []

            # add/remove for all eval scenes keys
            if "test_num" not in doc['keys']:
                keys_to_add.append("test_num")
            if "scene_part_num" in doc['keys']:
                keys_to_remove.append("scene_part_num")

            # add/remove for eval 3+ scenes keys only
            if "3" in doc['name']:
                # add
                if "goal.sceneInfo.hypercubeId" not in doc['keys']:
                    keys_to_add.append("goal.sceneInfo.hypercubeId")

                # remove
                if "goal.sceneInfo.sequenceId" in doc['keys']:
                    keys_to_remove.append("goal.sceneInfo.sequenceId")
                if "sequenceNumber" in doc['keys']:
                    keys_to_remove.append("sequenceNumber")
                if "sceneNumber" in doc['keys']:
                    keys_to_remove.append("sceneNumber")

            collection.update_one(
                {"_id": ObjectId(doc["_id"])},
                {"$push": {'keys': {"$each": keys_to_add}}},
                True)
            collection.update_one(
                {"_id": ObjectId(doc["_id"])},
                {"$pull": {'keys': {"$in": keys_to_remove}}},
                True)


def update_mcs_history_keys():
    logging.info("Begin Processing mcs_history_keys...")
    collection = mongoDB["mcs_history_keys"]

    documents = list(collection.find({}))
    logging.info("Found " + str(len(documents)) + " results")

    for doc in documents:
        if "scene_part_num" in doc["keys"]:
            collection.update_one(
                {"_id": ObjectId(doc["_id"])},
                {"$push": {'keys': "test_num"}},
                True)
            collection.update_one(
                {"_id": ObjectId(doc["_id"])},
                {"$pull": {'keys': "scene_part_num"}},
                True)


def update_mcs_scenes_keys():
    logging.info("Begin Processing mcs_scenes_keys...")
    collection = mongoDB["mcs_scenes_keys"]
    keys_to_remove = []
    keys_to_add = []

    documents = list(collection.find({}))
    logging.info("Found " + str(len(documents)) + " results")

    for doc in documents:

        # check keys to add
        if "test_num" not in doc["keys"]:
            keys_to_add.append("test_num")
        if "goal.sceneInfo.hypercubeId" not in doc["keys"]:
            keys_to_add.append("goal.sceneInfo.hypercubeId")

        # check keys to remove
        if "scene_part_num" in doc["keys"]:
            keys_to_remove.append("scene_part_num")
        if "goal.sceneInfo.sequenceId" in doc["keys"]:
            keys_to_remove.append("goal.sceneInfo.sequenceId")
        if "sequenceNumber" in doc["keys"]:
            keys_to_remove.append("sequenceNumber")
        if "sceneNumber" in doc["keys"]:
            keys_to_remove.append("sceneNumber")

        collection.update_one(
            {"_id": ObjectId(doc["_id"])},
            {"$push": {'keys': {"$each": keys_to_add}}},
            True)
        collection.update_one(
            {"_id": ObjectId(doc["_id"])},
            {"$pull": {'keys': {"$in": keys_to_remove}}},
            True)


def delete_old_saved_query():
    logging.info("Deleting single saved query...")
    collection = mongoDB["savedQueries"]

    collection.delete_one(
        {"_id": ObjectId("60008951c9ef6d5e7a77eb65")})


# one time run script (MCS-520)
def main():
    update_scene_num_refs_history_eval_2()
    update_scene_num_refs_history_eval_3()
    update_scene_num_refs_scenes_eval_2()
    update_scene_num_refs_scenes_eval_3()

    update_collection_keys()
    update_mcs_history_keys()
    update_mcs_scenes_keys()
    delete_old_saved_query()


if __name__ == "__main__":
    main()
