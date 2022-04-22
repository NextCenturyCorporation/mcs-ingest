#
# Class that runs a scripted movement around the room
#

import json
import logging

import machine_common_sense as mcs
from machine_common_sense import Action

from path_plotter import PathPlotter


DEFAULT_ROOM_DIMENSIONS = {'x': 10, 'y': 3, 'z': 10}


def key_to_movement(key):
    """Convert a character key to an instruction that the controller
    understands.  See Action to see the keys.  """
    for action in Action:
        if key == action._key:
            val = action._value_
            logging.debug(f"action {val}")

            if val == 'OpenObject' or \
                    val == 'CloseObject' or \
                    val == 'PickupObject':
                return val, {
                    'objectImageCoordsX': 320.,
                    'objectImageCoordsY': 240.
                }
            return val, {}

    if key == 'X':
        _ = input("waiting")
        return 'Pass', {}

    logging.warning(f"Unrecognized: {key}")
    return 'Pass', {}


def replace_short_hand(code):
    """Allow short-hand for movements.  W means forward 10 spaces;
    L and R, 90 degrees;  X means wait for input (for debugging)"""
    newcode = code.replace(" ", "")
    newcode = newcode.replace('W', "wwwwwwwwww")
    newcode = newcode.replace('L', "jjjjjjjjj")
    newcode = newcode.replace('R', "lllllllll")
    return newcode


def interactive_cb(step_metadata, runner_script):
    '''  Rather than using a string to represent
    movements, get interactive input'''
    x = input()
    return key_to_movement(x)


def decode_moves(step, code):
    newcode = replace_short_hand(code)

    if step >= len(newcode):
        return None, None
    key = newcode[step]
    return key_to_movement(key)


class DataGenRunnerScript():

    def __init__(self, scene_filepath, name, action_callback):
        self.controller = mcs.create_controller(
            config_file_or_dict='config_no_debug.ini')
        if not self.controller:
            raise Exception("Unable to create controller")
        self.callback = action_callback
        self.name = name
        self.scene_filepath = scene_filepath

    def run_scene(self):

        with open(self.scene_filepath) as scene_file:
            scene = json.load(scene_file)
            dim = scene.get("roomDimensions", DEFAULT_ROOM_DIMENSIONS)
            x_size = dim.get("x")
            y_size = dim.get("y")
            z_size = dim.get("z")

            plotter = PathPlotter(team="", scene_name=self.name,
                                  plot_width=600, plot_height=450,
                                  x_size=x_size, y_size=y_size,
                                  z_size=z_size)

            scene_data = mcs.load_scene_json_file(self.scene_filepath)
            if not scene_data:
                return
            if isinstance(scene_data, tuple):
                scene_data = scene_data[0]
            scene_data['name'] = self.name
            step_metadata = self.controller.start_scene(scene_data)
            action, params = self.callback(step_metadata, self)

            plotter.plot(step_metadata.__dict__, step_metadata.step_number)

            while action is not None:
                step_metadata = self.controller.step(action, **params)

                logging.debug("return status of action:" +
                              f"{step_metadata.return_status}")
                plotter.plot(step_metadata.__dict__, step_metadata.step_number)
                if step_metadata is None:
                    break
                action, params = self.callback(step_metadata, self)

            img = plotter.get_image()
            img.save(self.name + "_path.gif")
            self.controller.end_scene()
            return scene_data['name']
