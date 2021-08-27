#
#  Generate data for testing unopenable scorecard calculation
#
#  Usage:    python scorecard_generate_revisit_data.py  mcs_unity_filepath  scene_filepath
#
#    Normal movement: wasd,   turns: jl,   up/down: ik
#    Group movement:  90 turn is L or R;  W is 10 steps fwd
import argparse
import json
import os

import machine_common_sense as mcs

from tests.generator.path_plotter import PathPlotter


def decode_movements(step, code):
    """Allow short-hand for movements.  W means forward 10 spaces;
    L and R, 90 degrees;  X means wait for input (for debugging)"""
    code = code.replace(" ", "")
    code = code.replace('W', "wwwwwwwwww")
    code = code.replace('L', "jjjjjjjjj")
    code = code.replace('R', "lllllllll")

    if step >= len(code):
        return None, None
    key = code[step]
    if key == 'w':
        return 'MoveAhead', {}
    if key == 'j':
        return 'RotateLeft', {}
    if key == 'l':
        return 'RotateRight', {}
    if key == 'X':
        _ = input("waiting")
        return 'Pass', None
    print("Unrecognized: " + key)
    return None, None


class DataGenRunnerScript():

    def __init__(self, mcs_unity_filepath, scene_filepath, name, action_callback):
        self.controller = mcs.create_controller(mcs_unity_filepath)
        if not self.controller:
            raise Exception("Unable to create controller")
        self.callback = action_callback
        self.name = name
        self.scene_filepath = scene_filepath

    def run_scene(self):

        with open(self.scene_filepath) as scene_file:
            scene = json.load(scene_file)
            x_size = scene.get("roomDimensions").get("x")
            y_size = scene.get("roomDimensions").get("y")
            z_size = scene.get("roomDimensions").get("z")

            plotter = PathPlotter(team="", scene_name=self.name,
                                  plot_width=600, plot_height=450,
                                  x_size=x_size, y_size=y_size,
                                  z_size=z_size)

            scene_data, status = mcs.load_scene_json_file(self.scene_filepath)
            if not scene_data:
                print(f"Result of loading scene: {status}")
                return
            scene_data['name'] = self.name
            step_metadata = self.controller.start_scene(scene_data)
            action, params = self.callback(step_metadata, self)

            plotter.plot(step_metadata.__dict__, step_metadata.step_number)

            while action is not None:
                step_metadata = self.controller.step(action, **params)
                plotter.plot(step_metadata.__dict__, step_metadata.step_number)
                if step_metadata is None:
                    break
                action, params = self.callback(step_metadata, self)

            img = plotter.get_image()
            img.save(self.name + "_path.gif")
            self.controller.end_scene("", 1)
            return scene_data['name']


def simple_loop_callback(step_metadata, runner_script):
    '''  Do a loop around the room, but not overlapping, so no revisit'''
    actions = "WWWW L WWWW L WWW L WWW L WWWWWW"
    return decode_movements(step_metadata.step_number, actions)


def loop_callback_with_revisit(step_metadata, runner_script):
    '''  Do a square loop around the room.  Should causes one revisit'''
    actions = "WWWW L WWW L WWW L WWW L WWWWW"
    return decode_movements(step_metadata.step_number, actions)


def loop_callback_with_spin(step_metadata, runner_script):
    ''' Go fwd, do a circle, do a loop around the room.  Causes one revisit'''
    actions = "WWW LLLL W L WW L W L WWW"
    return decode_movements(step_metadata.step_number, actions)


def come_from_behind(step_metadata, runner_script):
    '''  Go behind a path and turn into it'''
    actions = "WW L WWW R WW L W L WWW L W L W R W"
    return decode_movements(step_metadata.step_number, actions)


def main(mcs_unity_filepath, scene_filepath):
    DataGenRunnerScript(mcs_unity_filepath, scene_filepath, 'zero_1', simple_loop_callback).run_scene()
    DataGenRunnerScript(mcs_unity_filepath, scene_filepath, 'one_1', loop_callback_with_revisit).run_scene()
    DataGenRunnerScript(mcs_unity_filepath, scene_filepath, 'one_2', loop_callback_with_spin).run_scene()
    DataGenRunnerScript(mcs_unity_filepath, scene_filepath, 'one_3', come_from_behind).run_scene()


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
