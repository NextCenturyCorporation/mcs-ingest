
import argparse
import logging
import os

from typing import List

from pymongo import MongoClient

import mcs_history_ingest

"""
Use for testing ingest changes locally (not for use in production) 

"""
def find_history_files(folder: str) -> dict:
    history_files = [
        f for f in os.listdir(
            folder) if str(f).endswith(".json")]
    history_files.sort()
    return history_files


def ingest_history_files(
        folder: str) -> None:
    client = MongoClient(
        'mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')

    history_files = find_history_files(folder)

    for file in history_files:
        mcs_history_ingest.automated_history_ingest_file(
            file, folder, "mcs", client)

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Ingest MCS History JSON files into Elasticsearch')
    parser.add_argument(
        '--folder',
        required=True,
        help='Folder location of files to important')

    args = parser.parse_args()

    ingest_history_files(
        args.folder
    )

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()