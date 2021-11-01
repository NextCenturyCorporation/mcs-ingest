#
#  Generate data for testing not moving toward a target
#
#  Usage:
#     python scorecard_generate_unopenable.py  mcs_unity  scene_file
#
#    (For scene_file, use tests/india_0003_17_debug)
#
#    Normal movement: wasd,   turns: jl,   up/down: ik.  Open is 3
#    Group movement:  90 turn is L or R;  W is 10 steps fwd
import argparse
import logging
import os

from test_data_generator.data_gen_runner import DataGenRunnerScript, \
    decode_moves


def not_moving_toward_zero_1(step_metadata, runner_script):
    """Head towards the target, see it, then have to go around
    a chair.  Requires 31 steps before it gets closer.  """
    actions = "WWWW L W R WW R wwwww"
    return decode_moves(step_metadata.step_number, actions)


def main(mcs_unity_filepath, scene_filepath):
    DataGenRunnerScript(mcs_unity_filepath, scene_filepath,
                        'not_moving_toward_zero_1',
                        not_moving_toward_zero_1).run_scene()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('mcs_unity_filepath')
    parser.add_argument('scene_filepath')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if not os.path.exists(args.mcs_unity_filepath):
        logging.warning(f"File {args.mcs_unity_filepath} does not exist")
        exit(1)
    if not os.path.exists(args.scene_filepath):
        logging.warning(f"File {args.scene_filepath} does not exist")
        exit(1)

    main(args.mcs_unity_filepath, args.scene_filepath)
