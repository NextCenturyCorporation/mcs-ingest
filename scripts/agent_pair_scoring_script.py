import logging
from pymongo import MongoClient
from bson.objectid import ObjectId

HISTORY_INDEX = "mcs_history"
EVAL_NAME = "Evaluation 3 Results"

# We might want to move mongo user/pass to new file
client = MongoClient('mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
mongoDB = client['mcs']

performers = [
    "IBM-MIT-Harvard-Stanford",
    "MESS-UCBerkeley",
    "OPICS (OSU, UU, NYU)"
]

agent_tasks = [
    "agents efficient action path lure",
    "agents efficient action time control",
    "agents object preference"
]


def find_pair_doc(documentscopy, scene_part_num, ground_truth):
    new_ground_truth = 0
    if ground_truth == 0:
        new_ground_truth = 1
    for new_doc in documentscopy:
        if (scene_part_num == new_doc["scene_part_num"]) and (
                new_ground_truth == new_doc["score"]["ground_truth"]):
            return new_doc


def scene_plausibility(answer, confidence):
    plausibility = 0
    if answer == "expected":
        plausibility = 1 * float(confidence)
    elif answer == "unexpected":
        plausibility = -1 * float(confidence)

    return plausibility


def process_pairing_scoring(performer: str, agent_task: str):
    logging.info("Begin Processing " + performer + ", " + agent_task)
    collection = mongoDB[HISTORY_INDEX]

    documents = list(collection.find(
        {
            "eval": EVAL_NAME,
            "performer": performer,
            "category_type": agent_task
        }))

    for doc in documents:
        pair_doc = find_pair_doc(
            documents, doc["scene_part_num"], doc["score"]["ground_truth"])
        pair_doc_plaus = 0
        if pair_doc is not None:
            pair_doc_plaus = scene_plausibility(
                pair_doc["score"]["classification"],
                pair_doc["score"]["confidence"])
        else:
            logging.warning("not found: " + doc["name"])
        doc["score"]["adjusted_confidence"] = scene_plausibility(
            doc["score"]["classification"], doc["score"]["confidence"])

        if doc["score"]["ground_truth"] == 1:
            doc["score"]["weighted_score_worth"] = 1
            if doc["score"]["adjusted_confidence"] > pair_doc_plaus:
                doc["score"]["weighted_score"] = 1
            else:
                doc["score"]["weighted_score"] = 0
        else:
            doc["score"]["weighted_score_worth"] = 0
            if pair_doc_plaus > doc["score"]["adjusted_confidence"]:
                doc["score"]["weighted_score"] = 1
            else:
                doc["score"]["weighted_score"] = 0

        collection.update_one(
            {"_id": ObjectId(doc["_id"])}, {"$set": doc}, True)


def main():
    for performer in performers:
        for task in agent_tasks:
            process_pairing_scoring(performer, task)


if __name__ == "__main__":
    main()
