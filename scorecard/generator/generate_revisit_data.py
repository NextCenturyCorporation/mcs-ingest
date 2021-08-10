#
#  Generate data for revisiting scorecard
#
#  Usage:    python generate_revisit_data.py [--level1=True] unity_runtime scene.json
#
# Look in machine_common_sense.Action for moves
#    Movement: wasd, turns: jl, up/down: ik
#    90 turn is L or R

import machine_common_sense as mcs

from scorecard.generator.path_plotter import PathPlotter

mcs_unity_filepath = "/home/clark/work/mcs/unity/4.1/MCS-AI2-THOR-Unity-App-v0.4.1.1.x86_64"
config_file = "mcs_config.ini"
scene_filepath = "/home/clark/work/mcs/mcs-ingest/scorecard/testdata/india_0015_12.json"


def decode_movements(step, code):
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
        x = input("waiting")
        return 'Pass', None
    print("Unrecognized: " + key)
    return None, None


class FakeEvent:
    """the plotter wants an ai2thor.event which contains metadata, but we don't have one, so
    create a FakeEvent object that contains metadata and pass that"""

    def __init__(self, metadata):
        self.metadata = metadata


class DataGenRunnerScript():

    def __init__(self, name, action_callback):
        self.controller = mcs.create_controller(mcs_unity_filepath, config_file)

        # self.controller._config.
        self.callback = action_callback
        self.name = name

    def run_scene(self):

        plotter = PathPlotter(team="", scene_name=self.name, plot_width=600, plot_height=450)

        scene_data, status = mcs.load_scene_json_file(scene_filepath)
        scene_data['name'] = self.name
        step_metadata = self.controller.start_scene(scene_data)
        action, params = self.callback(step_metadata, self)

        plotter.plot(FakeEvent(step_metadata), step_metadata.step_number)

        while action is not None:
            step_metadata = self.controller.step(action, **params)
            plotter.plot(FakeEvent(step_metadata), step_metadata.step_number)
            if step_metadata is None:
                break
            action, params = self.callback(step_metadata, self)

        img = plotter.get_image()
        img.save(self.name + "_path.gif")
        self.controller.end_scene("", 1)
        return scene_data['name']


def simple_loop_callback(step_metadata, runner_script):
    '''  Do a square loop around the room.  Should not causes revisit'''
    actions = "WWWW L WWWW L WWW L WWW L WWWWWW"
    return decode_movements(step_metadata.step_number, actions)


def main():
    DataGenRunnerScript('zero_1', simple_loop_callback).run_scene()


if __name__ == "__main__":
    main()
