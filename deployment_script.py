from pymongo import MongoClient
from scripts._0_4_3_add_admin_users import add_admins

# We might want to move mongo user/pass to new file
client = MongoClient(
    'mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
mongoDB = client['mcs']
VERSION_COLLECTION = "mcs_version"

# Change this version if running a new deploy script
# Make sure the first two numbers match the current MCS API Release
db_version = "0.4.3"


def check_version():
    collection = mongoDB[VERSION_COLLECTION]
    version_obj = collection.find_one()
    # return true if it is a newer db version
    return db_version > version_obj['version']


def update_db_version():
    collection = mongoDB[VERSION_COLLECTION]
    version_obj = collection.find_one()
    version_obj['version'] = db_version
    collection.replace_one({"_id": version_obj["_id"]}, version_obj)


def main():
    if(check_version()):
        print("New db version, execute scripts")
        # Place scripts here to run
        add_admins(mongoDB)

        # Now update db version
        update_db_version()
    else:
        print("Script does not need to run, already updated.")


if __name__ == "__main__":
    main()
