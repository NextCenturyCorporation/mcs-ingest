#
#  Generate some test files for the scorecard calculation
#
import json

from machine_common_sense import SceneHistory, HistoryWriter


def create_revisitor():
    """
    Create a datafile that goes one way across floor, then goes the other way,
    so that it crosses.  Should verify that it revisits.
    """

    history = {}
    steps = []

    for step_num in range(1, 100):
        step_dict = {'step': step_num}
        metadata = SceneHistory()
        metadata.position = {'x': 0.5, 'y': 1.0, 'z': (0.5 * (step_num * 0.07))}
        step_dict['output'] = metadata
        steps.append(step_dict)
    history['steps'] = steps

    scene_config_data = { 'name': 'test'}
    history_writer = HistoryWriter(scene_config_data)
    history_writer.write_history_file(.3, .2)

    with open("../revisitor.json", "a+") as revisitor_file:
        revisitor_file.write(json.dumps(history, indent=4))


if __name__ == "__main__":
    create_revisitor()
