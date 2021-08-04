#
#  Generate some test files for the scorecard calculation
#
import json

from machine_common_sense import SceneHistory, HistoryWriter, StepMetadata
from machine_common_sense.config_manager import SceneConfigurationSchema


def create_revisitor():
    """
    Create a datafile that goes one way across floor, then goes the other way,
    so that it crosses.  Should verify that it revisits.
    """
    scene_config_data = SceneConfigurationSchema()
    scene_config_data.name = "test"
    scene_config_data.screenshot = False
    history_writer = HistoryWriter(scene_config_data)
    for step_number in range(1, 100):
        step_output = StepMetadata(
            position = {'x': 0.5, 'y': 1.0, 'z': (0.5 * (step_number * 0.07))}
        )
        history_item = SceneHistory(
            step=step_number,
            output=step_output)
        history_writer.add_step(history_item)

    history_writer.write_history_file(.3, .2)

    # with open("../testdata/revisitor.json", "a+") as revisitor_file:
    #     revisitor_file.write(json.dumps(history, indent=4))


if __name__ == "__main__":
    create_revisitor()
