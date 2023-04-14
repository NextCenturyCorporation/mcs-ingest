from pymongo import MongoClient
import argparse
import sys
sys.path.insert(1, '../')
import create_collection_keys 

# Script Usage
# python update_collection_keys_if_missing.py eval_6_results "Evaluation 6 Results"


def update_collection_keys(collection_name: str, eval_name: str):
    client = MongoClient('mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
    mongoDB = client['mcs'] 

    print("Begin Updating Keys: " + collection_name + ", " + eval_name)
    create_collection_keys.find_collection_keys(collection_name, eval_name, mongoDB)
    print("Keys have finished updating.")


def main():
    parser = argparse.ArgumentParser('Update collection keys for Evaluation')
    parser.add_argument('collection_name', help='Collection Name ex(eval_6_results)')
    parser.add_argument('eval_name', help='Display String for Eva/Scene Name \
                        ex(Evaluation 6 Results)')
    args = parser.parse_args()

    if args.collection_name and args.eval_name:
        update_collection_keys(args.collection_name, args.eval_name)
    else:
        print("Error: collection_name and eval_name arguments required")


if __name__ == "__main__":
    main()