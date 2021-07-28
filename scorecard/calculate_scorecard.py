#
#  Driver program for calculating the scorecard
#


import argparse
import os

from scorecard.scorecard import Scorecard


def process(json_filename):
    scorecard = Scorecard(json_filename)
    scorecard.calc_revisiting()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('history_json_file', help="History JSON file, found in SCENE_HISTORY/")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if not os.path.exists(args.history_json_file):
        print(f"File {args.history_json_file} does not exist")
        exit(1)

    process(args.history_json_file)
