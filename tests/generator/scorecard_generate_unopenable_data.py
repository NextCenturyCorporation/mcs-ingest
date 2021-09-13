#
#  Generate data for testing unopenable scorecard calculation
#
#  Usage:    python scorecard_generate_revisit_data.py  mcs_unity_filepath  scene_filepath
#
#    (For scene_file, use tests/golf_0018_15_debug.json)
#
#    Normal movement: wasd,   turns: jl,   up/down: ik
#    Group movement:  90 turn is L or R;  W is 10 steps fwd
import argparse
import os

from tests.generator.data_gen_runner import decode_movements, DataGenRunnerScript


def simple_loop_callback(step_metadata, runner_script):
    '''  Do a loop around the room, but not overlapping, so no revisit'''
    actions = "WWWW L WWWW L WWW L WWW L WWWWWW"
    return decode_movements(step_metadata.step_number, actions)


def main(mcs_unity_filepath, scene_filepath):
    DataGenRunnerScript(mcs_unity_filepath, scene_filepath, 'three_1', simple_loop_callback).run_scene()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('mcs_unity_filepath')
    parser.add_argument('scene_filepath')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if not os.path.exists(args.mcs_unity_filepath):
        print(f"File {args.mcs_unity_filepath} does not exist")
        exit(1)
    if not os.path.exists(args.scene_filepath):
        print(f"File {args.scene_filepath} does not exist")
        exit(1)

    main(args.mcs_unity_filepath, args.scene_filepath)
