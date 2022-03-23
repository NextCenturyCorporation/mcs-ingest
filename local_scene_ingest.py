import argparse
import logging
import os

from pymongo import MongoClient
import mcs_scene_ingest

"""
Use for testing ingest changes locally (not for use in production) 

"""
def ingest_scene_files(folder: str) -> None:
    scene_files = find_scene_files(folder)
    client = MongoClient(
        'mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')

    for file in scene_files:
        mcs_scene_ingest.automated_scene_ingest_file(file, folder, "mcs", client)

def find_scene_files(folder: str) -> dict:
    scene_files = [
        f for f in os.listdir(
            folder) if str(f).endswith(mcs_scene_ingest.SCENE_DEBUG_EXTENSION)]
    scene_files.sort()
    return scene_files


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Ingest MCS Scene JSON files into database')
    parser.add_argument(
        '--folder',
        required=True,
        help='Folder location of files to important')

    args = parser.parse_args()
    ingest_scene_files(args.folder)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()