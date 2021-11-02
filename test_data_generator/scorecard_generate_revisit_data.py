#
#  Generate data for testing revisiting scorecard calculation
#
#  Usage:
#    python scorecard_generate_revisit_data.py  mcs_unity_file  scene_file
#
#    (For scene_file, use tests/india_0003_17_debug.json)
#
#    Normal movement: wasd,   turns: jl,   up/down: ik
#    Group movement:  90 turn is L or R;  W is 10 steps fwd
import argparse
import logging
import os

from test_data_generator.data_gen_runner import (
    decode_moves,
    DataGenRunnerScript
)


def simple_loop_callback(step_metadata, runner_script):
    '''  Do a loop around the room, but not overlapping, so no revisit'''
    actions = "WWWW L WWWW L WWW L WWW L WWWWWW"
    movement = decode_moves(step_metadata.step_number, actions)

    # DEBUGGING, this allows us to single-step through the scene
    # print(f"{step_metadata.step_number}  {movement}")
    # getinput = input()
    return movement


def loop_callback_with_revisit(step_metadata, runner_script):
    '''  Do a square loop around the room.  Should causes one revisit'''
    actions = "WWWW L WWW L WWW L WWW L WWWWW"
    return decode_moves(step_metadata.step_number, actions)


def loop_callback_with_spin(step_metadata, runner_script):
    ''' Go fwd, do a circle, do a loop around the room.  Causes one revisit'''
    actions = "WWW LLLL W L WW L W L WWW"
    return decode_moves(step_metadata.step_number, actions)


def come_from_behind(step_metadata, runner_script):
    '''  Go behind a path and turn into it'''
    actions = "WW L WWW R WW L W L WWW L W L W R W"
    return decode_moves(step_metadata.step_number, actions)


def main(mcs_unity_filepath, scene_filepath):
    ''' Call the script several times, passing in a different set of
    movements.  Naming scheme:
                      revisit_one_1
                          |    |  +-- example number
                          |    +----- how many revisits
                          +---------- this is a revisit example
    '''
    DataGenRunnerScript(mcs_unity_filepath, scene_filepath,
                        'revisit_zero_1',
                        simple_loop_callback).run_scene()
    DataGenRunnerScript(mcs_unity_filepath, scene_filepath,
                        'revisit_one_1',
                        loop_callback_with_revisit).run_scene()
    DataGenRunnerScript(mcs_unity_filepath, scene_filepath,
                        'revisit_one_2',
                        loop_callback_with_spin).run_scene()
    DataGenRunnerScript(mcs_unity_filepath, scene_filepath,
                        'revisit_one_3',
                        come_from_behind).run_scene()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('mcs_unity_filepath')
    parser.add_argument('scene_filepath')
    return parser.parse_args()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    args = parse_args()
    if not os.path.exists(args.mcs_unity_filepath):
        logging.warning(f"File {args.mcs_unity_filepath} does not exist")
        exit(1)
    if not os.path.exists(args.scene_filepath):
        logging.warning(f"File {args.scene_filepath} does not exist")
        exit(1)

    main(args.mcs_unity_filepath, args.scene_filepath)
