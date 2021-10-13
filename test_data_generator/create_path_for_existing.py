#
# Create a top-down plot so that we can visualize the non-generated data.
#
# usage:
#    create_path_for_existing.py  scene_file  output_json_file
import argparse
import json
import logging
import os

from test_data_generator.path_plotter import PathPlotter


def run_scene(output_json_file: str,
              x_size: int, y_size: int, z_size: int):
    with open(output_json_file) as history_file:
        history = json.load(history_file)
        name = history.get("info").get("name")
        plotter = PathPlotter(team="", scene_name=name,
                              plot_width=600, plot_height=450,
                              x_size=x_size, y_size=y_size,
                              z_size=z_size)

        steps_list = history['steps']

        for single_step in steps_list:
            step_metadata = single_step['output']
            step_num = step_metadata['step_number']
            plotter.plot(step_metadata, step_num)

        img = plotter.get_image()
        img.save(name + "_path.gif")


def make_plots_for_files(scene_file_path, output_json_file):
    # Get the room dimensions
    with open(scene_file_path) as scene_file:
        scene = json.load(scene_file)

        x_size = scene.get("roomDimensions").get("x")
        y_size = scene.get("roomDimensions").get("y")
        z_size = scene.get("roomDimensions").get("z")
        run_scene(output_json_file, x_size, y_size, z_size)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('scene_file_path')
    parser.add_argument('output_json_file')
    return parser.parse_args()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    args = parse_args()
    if not os.path.exists(args.scene_file_path):
        logging.warning(f"File {args.scene_file_path} does not exist")
        exit(1)
    if not os.path.exists(args.output_json_file):
        logging.warning(f"File {args.output_json_file} does not exist")
        exit(1)

    make_plots_for_files(args.scene_file_path, args.output_json_file)
