#
#  Driver program for calculating the scorecard
#
# By default it calculates the scorecard for all the files in the passed
# json file, containing ground truth.
#

import argparse
import os

from scorecard import Scorecard

DATADIR = 'generator/SCENE_HISTORY'

def process(basefilename: str, num_revisit: int, dir='') -> Scorecard:
    scorecard = Scorecard(basefilename)
    num_revisit_calc = scorecard.calc_revisiting()
    print(f"File: {basefilename}  ground_truth: {num_revisit}  Calculated: {num_revisit_calc}")
    return scorecard


def find_fullpath(basefilename: str, dir: str) -> os.path:
    for file in os.listdir(dir):
        if file.startswith(basefilename):
            full_path = os.path.join(dir, file)
            return full_path


def process_all_ground_truth(ground_truth_file: str):
    with open(ground_truth_file) as f:
        lines = f.readlines()
        for line in lines:
            if line[0] == "#":
                continue
            vals = line.split(" ")
            basefilename = vals[0].strip()
            num_revisit = int(vals[1].strip())
            full_path = find_fullpath(basefilename, DATADIR)
            if not full_path:
                print(f"Unable to find {DATADIR} and {basefilename} found: {full_path}")
                continue
            print(f"From {DATADIR} and {basefilename} found: {full_path}")
            process(full_path, num_revisit)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('ground_truth_file', help="History JSON file, found in SCENE_HISTORY/")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if not os.path.exists(args.ground_truth_file):
        print(f"File {args.ground_truth_file} does not exist")
        exit(1)

    process_all_ground_truth(args.ground_truth_file)
