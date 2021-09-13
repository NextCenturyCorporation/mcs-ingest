import json

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
