#
# path_plotter plots the path of an actor in the room, so we can visualize it.  It produces
# a single image showing the entire path (rather than a video based on multiple images,
# one per step, as was done in machine_common_sense.plotter.py)
#

import io
import math

import PIL
import matplotlib
from matplotlib import pyplot

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from typing import Dict, NamedTuple, List


class XZHeading(NamedTuple):
    x: float
    z: float


class Robot(NamedTuple):
    x: float
    y: float
    z: float
    rotation: float


class Object(NamedTuple):
    held: bool
    visible: bool
    uuid: str
    color: str
    bounds: list


class PathPlotter():
    ROBOT_PLOT_WIDTH = 0.02
    ROBOT_PLOT_LABEL = "robot"
    ROBOT_COLOR = 'xkcd:gray'
    DEFAULT_COLOR = "xkcd:black"
    HEADING_LENGTH = 0.4
    BORDER = 0.05

    def __init__(self, team: str, scene_name: str,
                 plot_width: int, plot_height: int,
                 x_size: int, y_size: int, z_size: int):
        self._team = team
        if '/' in scene_name:
            scene_name = scene_name.rsplit('/', 1)[1]
        self._scene_name = scene_name
        self._plot_width = plot_width
        self._plot_height = plot_height
        self._x_size = x_size
        self._y_size = y_size
        self._z_size = z_size
        self.plt = self._initialize_plot(step_number=0)

    def plot(self, metadata,
             step_number: int,
             goal_id: str = None
             ) -> PIL.Image.Image:

        self._draw_robot(metadata)

    def get_image(self):
        img = self._export_plot(self.plt)
        self.plt.close()
        return img

    def _find_plottable_objects(
            self, metadata) -> List:
        """Find plottable objects from the scene data.

        Plottable objects include normal scene objects as well as
        occluder and wall structural objects.
        """
        structural_objects = metadata.get('structural_object_list',
                                          [])
        filtered_structural_objects = [
            obj for obj in structural_objects
            if not obj.get('objectId', '').startswith('ceiling') and not
            obj.get('objectId', '').startswith('floor')
        ]
        objects = metadata.get('objects', [])
        return filtered_structural_objects + objects

    def _initialize_plot(self, step_number: int):
        """Create the plot"""
        plt.xlim(-self._x_size / 2, self._x_size / 2)
        plt.ylim(-self._z_size / 2, self._z_size / 2)
        plt.title(f"{self._team} {self._scene_name}")
        return plt

    def _export_plot(self, plt: matplotlib.pyplot) -> PIL.Image.Image:
        """Export the plot to a PIL Image"""
        fig = self.plt.gcf()
        buf = io.BytesIO()
        fig.savefig(buf)
        buf.seek(0)
        img = PIL.Image.open(buf)
        # resize image to match screen dimensions
        # current video recorders require it for now
        return img.resize((self._plot_width, self._plot_height))

    def _draw_robot(self, robot_metadata: Dict) -> None:
        """Plot the robot position and heading"""
        if robot_metadata is None:
            return None
        robot = self._create_robot(robot_metadata)
        self._draw_robot_position(robot)
        self._draw_robot_heading(robot)

    def _draw_robot_position(self, robot: Robot) -> None:
        """Draw the robot's scene XZ position in the plot"""
        circle = self.plt.Circle(
            (robot.x, robot.z),
            radius=self.ROBOT_PLOT_WIDTH,
            color=self.ROBOT_COLOR,
            label=self.ROBOT_PLOT_LABEL)
        self.plt.gca().add_patch(circle)

    def _draw_robot_heading(self, robot: Robot) -> None:
        """Draw the heading vector starting from the robot XZ position"""
        heading = self._calculate_heading(
            rotation_angle=360.0 - robot.rotation,
            heading_length=self.HEADING_LENGTH
        )
        heading = self.plt.Line2D((robot.x, robot.x + heading.x),
                                  (robot.z, robot.z + heading.z),
                                  color=self.ROBOT_COLOR,
                                  lw=1)
        self.plt.gca().add_line(heading)

    def _calculate_heading(self, rotation_angle: float,
                           heading_length: float) -> XZHeading:
        """Calculate XZ heading vector from the rotation angle"""
        s = math.sin(math.radians(rotation_angle))
        c = math.cos(math.radians(rotation_angle))
        vec_x = 0 * c - heading_length * s
        vec_z = 0 * s + heading_length * c
        return XZHeading(vec_x, vec_z)

    def _create_robot(self, robot_metadata: Dict) -> Robot:
        '''Extract robot position and rotation information from the metadata'''
        position = robot_metadata.get('position', None)
        if position is not None:
            x = position.get('x', None)
            y = position.get('y', None)
            z = position.get('z', None)
        else:
            x = 0.0
            y = 0.0
            z = 0.0

        rotation_y = robot_metadata.get('rotation', None)

        return Robot(x, y, z, rotation_y)

    def _convert_color(self, color: str) -> str:
        """Convert color string to xkcd string"""
        # use default of black if no color present
        if not color:
            color = 'black'
        # white color does not show up in plot but ivory does
        if color == 'white':
            color = 'ivory'
        # prefix with xkcd string
        return 'xkcd:' + color
