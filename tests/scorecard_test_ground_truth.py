#
# Driver program for testing the scorecard.
#
# By default it calculates the scorecard for all the ground truth in the passed
# text file.
#

import argparse
import os

from scorecard.scorecard import Scorecard

DATADIR = ['generator/SCENE_HISTORY/', '../tests/']


def process(json_filepath: str, num_revisit: int, dir='') -> Scorecard:
    """Process a particular json file, compare to ground truth"""
    scorecard = Scorecard(json_filepath)
    num_revisit_calc = scorecard.calc_revisiting()
    print(f"File: {json_filepath}  ground_truth: {num_revisit}" +
          f"  Calculated: {num_revisit_calc}")
    return scorecard


def find_fullpath(basefilename: str, dirs: []) -> os.path:
    for dir in dirs:
        for file in os.listdir(dir):
            if file.startswith(basefilename):
                full_path = os.path.join(dir, file)
                return full_path


def process_all_ground_truth(ground_truth_file: str):
    passed = 0
    failed = 0
    missing = 0

    with open(ground_truth_file) as f:
        lines = f.readlines()
        for line in lines:
            if line[0] == "#":
                continue
            vals = line.split()
            basefilename = vals[0].strip()
            gt_revisits = int(vals[1].strip())
            full_path = find_fullpath(basefilename, DATADIR)
            if not full_path:
                print(f"Unable to find {DATADIR} and " +
                      f"{basefilename} found: {full_path}")
                missing += 1
                continue
            print(f"From {DATADIR} and {basefilename} found: {full_path}")
            scorecard = process(full_path, gt_revisits)
            calc_revisit = scorecard.get_revisits()
            if gt_revisits == calc_revisit:
                passed += 1
            else:
                failed += 1

    print(f"\nPassed: {passed}  Failed: {failed}  Missing: {missing}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ground_truth_file',
                        default='ground_truth.txt')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if not os.path.exists(args.ground_truth_file):
        print(f"File {args.ground_truth_file} does not exist")
        exit(1)

    process_all_ground_truth(args.ground_truth_file)