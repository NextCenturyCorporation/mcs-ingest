import json
import os
import sys
import argparse
import mcs_scene_schema

from mcs_elasticsearch import MCSElasticSearch

def load_scene_file(folder: str, file_name: str) -> dict:
    with open(os.path.join(folder, file_name)) as json_file:
        return json.load(json_file)


def ingest_files(folder: str, eval_name: str, performer: str) -> None:
    schema = mcs_scene_schema.get_scene_schema()
    #TODO: Update this file so that you dynamically can set an arg for mcs_scenes, scene_history, etc, that will use an appropriate scheme file
    elastic_search = MCSElasticSearch("mcs_scenes", eval_name, True, schema)

    scene_files = [f for f in os.listdir(folder) if "debug" in str(f) and str(f).endswith(".json")]
    scene_files.sort()

    ingest_scenes = []

    for file in scene_files:
        print("Ingest scene file: {}".format(file))
        scene = load_scene_file(folder, file)
        scene["eval"] = eval_name
        scene["performer"] = performer

        #TODO: update index_dict to use args depending on what you are ingesting so this file is more dynamic
        index_dict = {
            "index": {
                "_index": "mcs_scenes",
                "_type": "scenes"
            }
        }

        ingest_scenes.append(index_dict)
        ingest_scenes.append(scene)

    elastic_search.bulk_upload(ingest_scenes)


def main(argv) -> None:
    parser = argparse.ArgumentParser(description='Ingest MCS Scene JSON files into Elasticsearch')
    parser.add_argument('--folder', required=True, help='Folder location of files to important')
    parser.add_argument('--eval_name', required=True, help='Name for this eval')
    parser.add_argument('--performer', required=False, help='Associate this ingest with a performer')
    #TODO: Add group arg that says which type of files are being ingested

    args = parser.parse_args(argv[1:])

    ingest_files(args.folder, args.eval_name, args.performer)


if __name__ == '__main__':
    main(sys.argv)