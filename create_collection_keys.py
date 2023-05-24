import re

# For the following step array fields, we want to save the 
# value contained in the first step.
STEPS_OUTPUT_FIELDS_TO_SAVE = [
    "steps.output.position.x",
    "steps.output.position.y",
    "steps.output.position.z",
    "steps.output.rotation",
    "steps.output.target.position.x",
    "steps.output.target.position.y",
    "steps.output.target.position.z"
]

# Added check for '-' for dash because some scorecard fields have object ids, same for
#  the numerical check.  None of our regular fields have '-' or numbers.
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
                elif append_string + item not in keys and "-" not in (append_string + item) \
                         and not bool(re.search(r'\d', (append_string + item))):
                    append_key(append_string + item, keys)

        elif append_string + item not in keys and "-" not in (append_string + item) \
                and not bool(re.search(r'\d', (append_string + item))):
            append_key(append_string + item, keys)

def append_key(key_string, keys):
    if(key_string.startswith("steps.") is False):
        keys.append(key_string)
    elif key_string in STEPS_OUTPUT_FIELDS_TO_SAVE:
        key_string = key_string[:6] + "0." + key_string[6:]
        if(key_string not in keys):
            keys.append(key_string)

def find_collection_keys(index: str, collection_name: str, mongoDB):
    collection = mongoDB[index]

    # Loop through documents to generate a keys collection to help
    #   speed in loading keys in UI
    keys = []
    documents = collection.find({"eval": collection_name})
    for doc in documents:
        recursive_find_keys(doc, keys, "")

    keys_dict = {'name': collection_name, 'keys': keys}
    collection = mongoDB["collection_keys"]
    result = collection.update_one(
        {"name": collection_name}, {"$set": keys_dict}, True)


def check_collection_has_key(collection_name: str, mongoDB):
    collection = mongoDB["collection_keys"]
    return collection.find_one({"name": collection_name})
