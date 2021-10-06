#
#  Generate data for testing re-openening a container
#
#  Usage:
#     python scorecard_generate_unopenable.py  mcs_unity  scene_file
#
#    (For scene_file, use tests/golf_0018_15_debug.json)
#
#    Normal movement: wasd,   turns: jl,   up/down: ik.  Open is 3
#    Group movement:  90 turn is L or R;  W is 10 steps fwd
import argparse
import logging
import os

from tests.generator.data_gen_runner import DataGenRunnerScript, decode_moves, replace_short_hand


def reopen_objects_callback_zero_1(step_metadata, runner_script):
    step = step_metadata.step_number
    # Open on the side
    part1 = "WWW  wwwww L kkkkk 3"

    # Now go around but do not look inside
    part2 = "R wwwwww L W L Wwww L W  L W"
    code = part1 + part2

    moves = replace_short_hand(code)
    return decode_moves(step, moves)


def reopen_objects_callback_one_1(step_metadata, runner_script):
    step = step_metadata.step_number
    # Open on the side
    part1 = "WWW  wwwww L kkkkk 3"

    # Now go around and look from other side
    part2 = "R Wwwwwww L W L Wwwwww L RR W"
    code = part1 + part2

    moves = replace_short_hand(code)
    return decode_moves(step, moves)


def main(mcs_unity_filepath, scene_filepath):
    DataGenRunnerScript(mcs_unity_filepath, scene_filepath,
                        'reopen_zero_1', reopen_objects_callback_zero_1).run_scene()

    DataGenRunnerScript(mcs_unity_filepath, scene_filepath,
                        'reopen_one_1', reopen_objects_callback_one_1).run_scene()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('mcs_unity_filepath')
    parser.add_argument('scene_filepath')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if not os.path.exists(args.mcs_unity_filepath):
        logging.warning(f"File {args.mcs_unity_filepath} does not exist")
        exit(1)
    if not os.path.exists(args.scene_filepath):
        logging.warning(f"File {args.scene_filepath} does not exist")
        exit(1)

    main(args.mcs_unity_filepath, args.scene_filepath)
