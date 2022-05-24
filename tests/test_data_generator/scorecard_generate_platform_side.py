#
#  Generate data for testing which platform side agent went down
#
#  Usage:
#     python scorecard_generate_platform_side.py  scene_file
#
#    (For scene_file, use test_data/prefix_0001_01_C4_debug.json)
#
#    Normal movement: wasd,   turns: jl,   up/down: ik.  Open is 3
#    Group movement:  90 turn is L or R;  W is 10 steps fwd
import argparse
import logging
import os

from data_gen_runner import (
    DataGenRunnerScript,
    decode_moves,
    replace_short_hand
)


def go_left_off_platform(step_metadata, runner_script):
    step = step_metadata.step_number
    # Go off to the left.
    part1 = "aaaaaaaaaaaaaaaaaa"

    moves = replace_short_hand(part1)
    return decode_moves(step, moves)


def go_right_off_platform(step_metadata, runner_script):
    step = step_metadata.step_number
    # Go off to the left.
    part1 = "dddddddddddddddddddd"

    moves = replace_short_hand(part1)
    return decode_moves(step, moves)


def main(scene_filepath):
    DataGenRunnerScript(scene_filepath,
                        'gen_platform_side_1',
                        go_right_off_platform).run_scene()

    DataGenRunnerScript(scene_filepath,
                        'gen_platform_side_2',
                        go_left_off_platform).run_scene()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('scene_filepath')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if not os.path.exists(args.scene_filepath):
        logging.error(f"File {args.scene_filepath} does not exist")
        exit(1)

    main(args.scene_filepath)
