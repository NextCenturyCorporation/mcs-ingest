#
#  Generate data for testing unopenable scorecard calculation
#
#  Usage:    python scorecard_generate_unopenable.py  mcs_unity_filepath  scene_filepath
#
#    (For scene_file, use tests/golf_0018_15_debug.json)
#
#    Normal movement: wasd,   turns: jl,   up/down: ik
#    Group movement:  90 turn is L or R;  W is 10 steps fwd
import argparse
import logging
import os

from tests.generator.data_gen_runner import DataGenRunnerScript, decode_movements


def open_objects_callback(step_metadata, runner_script):
    '''  Generate output that has 2 successful opens, 1 NOT_RECEPTACLE, 1 NOT_OPENABLE'''

    step = step_metadata.step_number
    part1 = "wwwwwjjjWlllWWwwss kkkkk 3 "
    # success -- right, fwd, diagonal left, fwd, diag right, fwd, try to open small box
    part2 = "iiiii R W jjj wwww lll WW kkkk s 3 "
    # NOT_RECEPTACLE --
    part3 = "iiii L wwwww 3"
    # NOT_OPENABLE
    part4 = "kkkllll W lll wwww kk 3"
    code = part1 + part2 + part3 + part4
    return decode_movements(step, code)


def main(mcs_unity_filepath, scene_filepath):
    DataGenRunnerScript(mcs_unity_filepath, scene_filepath, 'unopenable_two', open_objects_callback).run_scene()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('mcs_unity_filepath')
    parser.add_argument('scene_filepath')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if not os.path.exists(args.mcs_unity_filepath):
        logging.warning(f"File {args.mcs_unity_filepath} does not exist")
        exit(1)
    if not os.path.exists(args.scene_filepath):
        logging.warning(f"File {args.scene_filepath} does not exist")
        exit(1)

    main(args.mcs_unity_filepath, args.scene_filepath)
