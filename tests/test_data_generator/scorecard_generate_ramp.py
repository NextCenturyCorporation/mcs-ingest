#
#  Generate data for testing ramps
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
    decode_moves,
    replace_short_hand
)


def ramp_up_down_abandon_fall(step_metadata, runner_script):
    step = step_metadata.step_number
    # Go up the ramp and turn around
    part1 = "WWWWWW RR"

    # Go down ramp
    part2 = "WWWWWW RR"

    # Abandon a ramp, going up
    part3 = "WWWWww ssssssssss ssssssssss ssssssssss ssssssssss ss"

    # Go up a ramp, turn and fall off
    part4 = "WWWWww L WW L WWWWww L WW L"

    # Go up ramp again.
    part5 = "WWWWWW RR"

    # Go down and abandon
    part6 = "WWwww ssssssssss ssssssssss sss"

    # Go down, turn, and fall off
    part7 = "WWww L WWWW"

    code = part1 + part2 + part3 + part4 + part5 + part6 + part7

    moves = replace_short_hand(code)
    return decode_moves(step, moves)


def main(scene_filepath):
    DataGenRunnerScript(scene_filepath,
                        'gen_ramps_all_moves',
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
