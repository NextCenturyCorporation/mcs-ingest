#
# Driver program for testing the scorecard.
#
# By default it calculates the scorecard for all the ground truth in the passed
# text file.
#

import argparse
import json
import logging
import os

from scorecard import Scorecard

HISTORY_DIR = './test_data/'
SCENE_DIR = './test_data/'


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


def find_fullpath_latest(basefilename: str, dir_name: str) -> os.path:
    '''Look in the passed directory for files with the appropriate
    basename.  Example: If passed 'reopen_one_1', it will return
    "reopen_one_1-20211013-093519.json" if it finds it.  If there
    are multiple files that match, it will return
    the most recent one.'''
    matching_files = []
    for file in os.listdir(dir_name):
        if file.startswith(basefilename):
            full_path = os.path.join(dir_name, file)
            matching_files.append(full_path)
    matching_files.sort(key=lambda x: os.path.getmtime(x))
    if len(matching_files) > 0:
        return matching_files.pop()
    return None


def compare_with_ground_truth(
        scorecard: Scorecard, gt_revisit: int,
        gt_unopenable: int, gt_relook: int,
        gt_not_moving_towards: int, gt_repeat_failed: int):
    ''' compare to ground truth (num_revisit)'''
    num_revisit_calc = scorecard.get_revisits()
    num_unopenable_calc = scorecard.get_unopenable()
    num_relook_calc = scorecard.get_relooks()
    num_not_moving_twd = scorecard.get_not_moving_towards()
    num_repeat_failed = scorecard.get_repeat_failed()

    logging.info(f"     revisit: {gt_revisit} {num_revisit_calc}" +
                 f"   unopenable: {gt_unopenable} {num_unopenable_calc}"
                 f"   relook: {gt_relook}  {num_relook_calc}"
                 f"  nottoward: {gt_not_moving_towards} {num_not_moving_twd}"
                 f"  repeatfailed: {gt_repeat_failed} {num_repeat_failed}")

    passed = 0
    failed = 0

    if gt_unopenable == num_unopenable_calc:
        passed += 1
    else:
        failed += 1

    if gt_revisit == num_revisit_calc:
        passed += 1
    else:
        failed += 1

    if gt_relook == num_relook_calc:
        passed += 1
    else:
        failed += 1

    if gt_not_moving_towards == num_not_moving_twd:
        passed += 1
    else:
        failed += 1

    if gt_repeat_failed == num_repeat_failed:
        passed += 1
    else:
        failed += 1

    return passed, failed


def process_line(line: str):
    if line[0] == "#":
        return 0, 0, 0
    vals = line.split()

    scenefile = vals[0].strip()
    basefilename = vals[1].strip()

    gt_revisits = int(vals[2].strip())
    gt_unopenable = int(vals[3].strip())
    gt_relook = int(vals[4].strip())
    gt_not_moving_towards = int(vals[5].strip())
    gt_repeat_failed = int(vals[6].strip())

    scene_filepath = find_fullpath_latest(scenefile, SCENE_DIR)
    if not scene_filepath:
        logging.warning(f"Unable to find {SCENE_DIR} and " +
                        f"{scenefile} found: {scene_filepath}")
        return 0, 0, 1

    history_filepath = find_fullpath_latest(basefilename, HISTORY_DIR)
    if not history_filepath:
        logging.warning(f"Unable to find '{basefilename}' in " +
                        f"{HISTORY_DIR}")
        return 0, 0, 1
    logging.info(f"Reporting on {history_filepath}")

    scorecard = get_scorecard(history_filepath, scene_filepath)
    p, f = compare_with_ground_truth(
        scorecard, gt_revisits, gt_unopenable,
        gt_relook, gt_not_moving_towards, gt_repeat_failed)
    logging.info(f"     results  pass: {p}   fail: {f}")
    return p, f, 0


def process_all_ground_truth(ground_truth_file: str):
    passed = 0
    failed = 0
    missing = 0

    with open(ground_truth_file) as f:
        lines = f.readlines()
        for line in lines:
            p, f, m = process_line(line)

            passed += p
            failed += f
            missing += m

    logging.info(f"\nPassed: {passed}  Failed: {failed}  Missing: {missing}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ground_truth_file',
                        default='tests/ground_truth.txt')
    return parser.parse_args()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    args = parse_args()

    if not os.path.exists(args.ground_truth_file):
        logging.warning(f"File {args.ground_truth_file} does not exist")
        exit(1)

    process_all_ground_truth(args.ground_truth_file)
