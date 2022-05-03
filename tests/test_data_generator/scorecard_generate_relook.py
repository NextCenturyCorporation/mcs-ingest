#
#  Generate data for testing re-looking into a container
#
#  Usage:
#     python scorecard_generate_relook.py  scene_file
#
#    (For scene_file, use tests/golf_0018_15_debug.json)
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


def relook_objects_zero_1(step_metadata, runner_script):
    step = step_metadata.step_number
    # Open on the side
    part1 = "WWW  wwwww L kkkkk 3"

    # Now go around but do not look inside
    part2 = "R wwwwww L W L Wwww L W  L W"
    code = part1 + part2

    moves = replace_short_hand(code)
    return decode_moves(step, moves)


def relook_objects_one_1(step_metadata, runner_script):
    step = step_metadata.step_number
    # Open on the side
    part1 = "WWW  wwwww L kkkkk 3"

    # Now go around and look from other side
    part2 = "R Wwwwwww L W L Wwwwww L RR W"
    code = part1 + part2

    moves = replace_short_hand(code)
    return decode_moves(step, moves)


def main(scene_filepath):
    DataGenRunnerScript(scene_filepath,
                        'gen_relook_zero_1',
                        relook_objects_zero_1).run_scene()

    DataGenRunnerScript(scene_filepath,
                        'gen_relook_one_1',
                        relook_objects_one_1).run_scene()


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