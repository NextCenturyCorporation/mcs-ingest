#
#  Generate data for testing counting of torques / push / pull / move / rotate
#
#  Usage:
#     python scorecard_generate_ramp.py  scene_file
#
#    (For scene_file, use test_data/ramps_eval_5_ex_1.json)
#
#    Normal movement: wasd,   turns: jl,   up/down: ik.  Open is 3
#    Group movement:  90 turn is L or R;  W is 10 steps fwd
import argparse
import logging
import os

from data_gen_runner import (
    DataGenRunnerScript,
    decode_moves
)


def ramp_up_down_abandon_fall(step_metadata, runner_script):
    step = step_metadata.step_number
    # Look down and 'Move' 3 times
    part1 = "kk 000 ww"

    # Push 2 times and pull 3 times
    part2 = "66 555"

    # torque 4 times, rotate 2 with another torque
    part3 = "8888 wwww k www 9 w8 w9 "

    # Above are all successful.  Make some unsuccessful
    part4 = "L 56890"

    moves = part1 + part2 + part3 + part4

    return decode_moves(step, moves)


def main(scene_filepath):
    DataGenRunnerScript(scene_filepath,
                        'gen_torques',
                        ramp_up_down_abandon_fall).run_scene()


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
