#
#  Generate data for testing revisiting scorecard calculation
#
#  Usage:
#    python scorecard_generate_revisit_data.py  mcs_unity_file  scene_file
#
#    Normal movement: wasd,   turns: jl,   up/down: ik
#    Group movement:  90 turn is L or R;  W is 10 steps fwd
import argparse
import logging
import os

from machine_common_sense import Action

from tests.test_data_generator.data_gen_runner import (
    DataGenRunnerScript,
    interactive_cb
)


def main(scene_filepath):
    for action in Action:
        logging.info(f"{action._key} -- {action._value_}")

    DataGenRunnerScript(scene_filepath,
                        'gen_interactive',
                        interactive_cb).run_scene()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('scene_filepath')
    return parser.parse_args()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    args = parse_args()
    if not os.path.exists(args.scene_filepath):
        logging.error(f"File {args.scene_filepath} does not exist")
        exit(1)

    main(args.scene_filepath)
