#
# Create a top-down plot so that we can visualize the
# non-generated data.
#
import json
import os

from tests.generator.path_plotter import PathPlotter

dir = 'SCENE_HISTORY'
files = ['india_0003.json']


def run_scene(name: str, filepath: str):
    plotter = PathPlotter(team="", scene_name=name,
                          plot_width=600, plot_height=450)

    with open(filepath) as history_file:
        history = json.load(history_file)

        steps_list = history['steps']

        for single_step in steps_list:
            step_metadata = single_step['output']
            step_num = step_metadata['step_number']
            plotter.plot(step_metadata, step_num)

        img = plotter.get_image()
        img.save(name + "_path.gif")


def make_plots_for_files():
    for file in files:
        full_path = os.path.join(dir, file)
        run_scene(file, full_path)


if __name__ == "__main__":
    make_plots_for_files()
