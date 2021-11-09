#
#  Generate data for testing repeated failed actions scorecard calculation
#
#  Usage:
#     python scorecard_generate_repeat_failed.py  mcs_unity  scene_file
#
#    (For scene_file, use tests/golf_0018_15_debug.json)
#
#    Normal movement: wasd,   turns: jl,   up/down: ik
#    Group movement:  90 turn is L or R;  W is 10 steps fwd
import argparse
import logging
import os

from test_data_generator.data_gen_runner import (
    DataGenRunnerScript,
    decode_moves
)


def open_different_ways(step_metadata, runner_script):
    '''  Generate output that has 3 unsuccessful opens:
    NOT_INTERACTABLE, NOT_OPENABLE, IS_OPENED_COMPLETELY'''

    step = step_metadata.step_number

    # This will put us in front of the object, but
    # not looking down
    part1 = "wwwwwjjjWlllwwwwwwwwww 3"

    # Look down, but too far away
    part2 = "kk 3"

    # Get closer, so works
    part3 = "wwwwww kkk 3"

    # Try to open again, get already opened
    part4 = "3"

    code = part1 + part2 + part3 + part4
    return decode_moves(step, code)


def pickup_fail_twice(step_metadata, runner_script):
    ''' Fail to pick up an unpickupable object twice. '''

    step = step_metadata.step_number

    # This will put us in front of the object, but
    # not looking down
    part1 = "wwwwwjjjWlllwwwwwwwwww "

    # Look down, but too far away
    part2 = "kk "

    # Get closer, so works
    part3 = "wwwwww kkk 4 4"

    code = part1 + part2 + part3
    return decode_moves(step, code)


def main(mcs_unity_filepath, scene_filepath):
    DataGenRunnerScript(mcs_unity_filepath, scene_filepath,
                        'repeat_failed_zero', open_different_ways).run_scene()

    DataGenRunnerScript(mcs_unity_filepath, scene_filepath,
                        'repeat_failed_one', pickup_fail_twice).run_scene()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('mcs_unity_filepath')
    parser.add_argument('scene_filepath')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if not os.path.exists(args.mcs_unity_filepath):
        logging.warning(f"File {args.mcs_unity_filepath} does not exist")
        exit(1)
    if not os.path.exists(args.scene_filepath):
        logging.warning(f"File {args.scene_filepath} does not exist")
        exit(1)

    main(args.mcs_unity_filepath, args.scene_filepath)
