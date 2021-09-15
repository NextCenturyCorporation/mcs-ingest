#
# Driver program for testing the scorecard.
#
# By default it calculates the scorecard for all the ground truth in the passed
# text file.
#

import argparse
import json
import os

from scorecard.scorecard import Scorecard

DATADIR = ['generator/SCENE_HISTORY/', '../tests/']



def get_scorecard(
        history_filepath: str, scene_filepath: str) -> Scorecard:
    """Process a particular json file,"""

    with open(history_filepath) as history_file:
        history = json.load(history_file)

    with open(scene_filepath) as scene_file:
        scene = json.load(scene_file)

    scorecard = Scorecard(history, scene)
    scorecard.score_all()
    return scorecard


def compare_with_ground_truth(
        scorecard: Scorecard, gt_revisit: int, gt_unopenable):
    ''' compare to ground truth (num_revisit)'''
    num_revisit_calc = scorecard.get_revisits()
    num_unopenable_calc = scorecard.get_unopenable()

    print(f" gt_revisit: {gt_revisit}  calc_revisit: {num_revisit_calc}" +
                 f" gt_unopenable: {gt_unopenable}  " +
                 "calc_unopenable: {num_unopenable_calc}")

    passed = 0
    failed = 0
    if gt_revisit == scorecard.get_revisits():
        passed += 1
    else:
        failed += 1

    if gt_unopenable == scorecard.get_unopenable():
        if gt_revisit == scorecard.get_revisits():
            passed += 1
        else:
            failed += 1
    return passed, failed


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

            scenefile = vals[0].strip()
            basefilename = vals[1].strip()

            gt_revisits = int(vals[2].strip())
            gt_unopenable = int(vals[3].strip())

            scene_filepath = find_fullpath(scenefile, DATADIR)
            if not scene_filepath:
                print(f"Unable to find {DATADIR} and " +
                      f"{scenefile} found: {scene_filepath}")
                missing += 1
                continue

            history_filepath = find_fullpath(basefilename, DATADIR)
            if not history_filepath:
                print(f"Unable to find {DATADIR} and " +
                      f"{basefilename} found: {history_filepath}")
                missing += 1
                continue

            scorecard = get_scorecard(
                history_filepath, scene_filepath)

            history_pass, history_fail = compare_with_ground_truth(
                scorecard, gt_revisits, gt_unopenable)

            passed += history_pass
            failed += history_fail

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
