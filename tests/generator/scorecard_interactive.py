#
#  Generate data for testing revisiting scorecard calculation
#
#  Usage:
#    python scorecard_generate_revisit_data.py  mcs_unity_file  scene_file
#
#    Normal movement: wasd,   turns: jl,   up/down: ik
#    Group movement:  90 turn is L or R;  W is 10 steps fwd
import argparse
import os

from machine_common_sense import Action

from tests.generator.data_gen_runner import DataGenRunnerScript, interactive_cb


def main(mcs_unity_filepath, scene_filepath):
    for action in Action:
        print(f"{action._key} -- {action._value_}")

    DataGenRunnerScript(mcs_unity_filepath, scene_filepath,
                        'interactive', interactive_cb).run_scene()


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
