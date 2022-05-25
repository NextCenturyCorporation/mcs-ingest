#
#  Generate data for testing which door was opened in a triple door scene
#
#  Usage:
#     python scorecard_generate_door_opened.py scene_file
#
#    (For scene_file, use test_data/prefix_0001_02_I1_debug.json)
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


def go_to_center_door(step_metadata, runner_script):
    step = step_metadata.step_number
    # Go toward the center door
    # use ` for pass, since spaces are stripped out
    step1 = "````````````````````````````````````````````````````````````````````````````"
    step2 = "WWWW3"
    
    moves = replace_short_hand(step1 + step2)
    return decode_moves(step, moves)

def go_to_left_door(step_metadata, runner_script):
    step = step_metadata.step_number
    # Go toward the center door
    # use ` for pass, since spaces are stripped out
    step1 = "````````````````````````````````````````````````````````````````````````````"
    step2 = "aaaaaaaaaaaaaaaaaaaaaa WWWW3"
    
    moves = replace_short_hand(step1 + step2)
    return decode_moves(step, moves)


def main(scene_filepath):
    DataGenRunnerScript(scene_filepath,
                        'gen_correct_door_ex',
                        go_to_center_door).run_scene()

    DataGenRunnerScript(scene_filepath,
                        'gen_incorrect_door_ex',
                        go_to_left_door).run_scene()



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
