from pymongo import MongoClient
from scripts._0_5_0_2_fix_incorrect_slice_info import update_slice_info

# We might want to move mongo user/pass to new file
VERSION_COLLECTION = "mcs_version"

# Change this version if running a new deploy script
# Make sure the first two numbers match the current MCS API Release
db_version = "0.5.0.2"


def check_version(mongoDB):
    collection = mongoDB[VERSION_COLLECTION]
    version_obj = collection.find_one()
    # return true if it is a newer db version
    return db_version > version_obj['version']


def update_db_version(mongoDB):
    collection = mongoDB[VERSION_COLLECTION]
    version_obj = collection.find_one()
    version_obj['version'] = db_version
    collection.replace_one({"_id": version_obj["_id"]}, version_obj)


def main():
    client = MongoClient(
        'mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
    mongoDB = client['mcs']
    if(check_version(mongoDB)):
        print("New db version, execute scripts")
        # Place scripts here to run
        update_slice_info(mongoDB)

        # Now update db version
        update_db_version(mongoDB)
    else:
        print("Script does not need to run on prod, already updated.")

    client = MongoClient(
        'mongodb://mongomcs:mongomcspassword@localhost:27017/dev')
    mongoDB = client['dev']
    if(check_version(mongoDB)):
        print("New db version, execute scripts")
        # Place scripts here to run
        update_slice_info(mongoDB)

        # Now update db version
        update_db_version(mongoDB)
    else:
        print("Script does not need to run on dev, already updated.")


if __name__ == "__main__":
    main()
