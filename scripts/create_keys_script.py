from pymongo import MongoClient

HISTORY_INDEX = "mcs_history"
SCENE_INDEX = "mcs_scenes"

# We might want to move mongo user/pass to new file
client = MongoClient('mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
mongoDB = client['mcs']


def recursive_find_keys(x, keys, append_string):
    key_list = list(x.keys())
    for item in key_list:
        if isinstance(x[item], dict):
            recursive_find_keys(x[item], keys, append_string + item + ".")
        elif isinstance(x[item], list):
            for arrayItem in x[item]:
                if isinstance(arrayItem, dict):
                    recursive_find_keys(
                        arrayItem, keys, append_string + item + ".")
                elif append_string + item not in keys:
                    keys.append(append_string + item)
        elif append_string + item not in keys:
            keys.append(append_string + item)


def find_collection_keys(index: str, collection_name: str):
    collection = mongoDB[index]

    # Loop through documents to generate a keys collection to help
    #   speed in loading keys in UI
    keys = []
    print(collection_name)
    documents = collection.find({"eval": collection_name})
    for doc in documents:
        recursive_find_keys(doc, keys, "")

    keys_dict = {}
    keys_dict["name"] = collection_name
    keys_dict["keys"] = keys

    collection = mongoDB["collection_keys"]
    result = collection.update_one(
        {"name": collection_name}, {"$set": keys_dict}, True)
    print(result)


def main():
    print("Starting Key Processing")
    # Example of calling find_collection_keys, we  changed this to
    #   run automatically but could still be useful for future

    # find_collection_keys(HISTORY_INDEX, "Evaluation 3.5 Results")
    # find_collection_keys(SCENE_INDEX, "Evaluation 3.5 Scenes")


if __name__ == "__main__":
    main()
