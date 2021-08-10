import json
import math
from dataclasses import dataclass

import numpy as np
# Assume that the entire room space goes from -5 to 5 in X and Z.  If this changes,
# then will need to change this line or read in from scene json file.
import pandas

SPACE_SIZE = 5.

# Grid Dimension determines how big our grid is for revisiting
GRID_DIMENSION = 0.5

# Direction limit:  Degrees difference that we allow before we count actors
# as facing in the same direction
DIRECTION_LIMIT = 21


class GridHistory:
    """A history of the times a grid has been visited"""
    def __init__(self):
        self.stepnums = []
        self.directions = []

    def add(self, stepnum: int, direction: int):
        self.stepnums.append(stepnum)
        self.directions.append(stepnum)

    def seen_before(self, stepnum: int, direction: int):
        for previous_direction in self.directions:
            diff = abs(previous_direction - direction)
            if diff < DIRECTION_LIMIT:
                return True
        return False

class Scorecard:
    """
    Scorecard calculates and holds information on several measures of performance for an agent moving
    in the active tasks.

    Reminder:   location in Unity is a left-handed, y-up axis orientation system.
    See:  https://docs.unity3d.com/Manual/class-Transform.html
    So we process (X,Z) locations.
    """

    def __init__(self, history_file_name):
        self.history_file_name = history_file_name
        with open(self.history_file_name) as history_file:
            self.history = json.load(history_file)

        # Size of the grid for calculating revisiting
        self.grid_dimension = GRID_DIMENSION
        self.grid_size = (int)(2 * SPACE_SIZE / self.grid_dimension)

        # Create the grid history and the counts
        self.grid = [[GridHistory() for j in range(self.grid_size)] for i in range(self.grid_size)]
        self.grid_counts = np.zeros([self.grid_size, self.grid_size])

        # Output values
        self.revisits = 0

    def calc_revisiting(self):

        steps_list = self.history['steps']

        step_num = 0
        single_step = steps_list[0]
        loc = single_step['output']['position']
        old_x, old_z = self.get_grid_by_location(loc['x'], loc['z'])

        for single_step in steps_list:
            step_num+= 1
            loc = single_step['output']['position']
            grid_x, grid_z = self.get_grid_by_location(loc['x'], loc['z'])
            # print(f"Step value: {single_step['step']}  Location is {loc}.    Grid loc is {grid_x} {grid_z}")

            grid_hist = self.grid[grid_x][grid_z]
            grid_hist.add(step_num, single_step['output']['rotation'])

            # If we did not change grid location (for example, change tilt, rotate, etc), do not count
            if old_x == grid_x and old_z == grid_z:
                continue

            self.grid_counts[grid_x, grid_z] += 1
            old_x, old_z = grid_x, grid_z

        # Ignore all the grid cells with 1's or 0's, by subtracting 1 and making 0 the minimum.
        self.grid_counts -= 1
        self.grid_counts = np.clip(self.grid_counts, 0, None)
        self.revisits = self.grid_counts.sum()

        self.print_grid()
        print(f"Total number of naive revisits: {self.revisits}")

        return self.revisits

    def get_grid_by_location(self, x, z):
        """ Given an x,z location, determine the (int) values for the grid location"""
        grid_x = (int)((SPACE_SIZE + x) / self.grid_dimension)
        grid_z = (int)((SPACE_SIZE + z) / self.grid_dimension)

        if grid_x < 0 or grid_x > self.grid_size - 1:
            print(f"Problem with x loc {x}.  got grid loc {grid_x}.  " +
                  "dim {self.grid_dimension} grid size {self.grid_size}")
        if grid_z < 0 or grid_z > self.grid_size - 1:
            print(f"Problem with y loc {z}.  got grid loc {grid_z}.  " +
                  "dim {self.grid_dimension} grid size {self.grid_size}")
        return (grid_x, grid_z)

    def print_grid(self):
        # Use a Pandas Dataframe to print it out
        df = pandas.DataFrame(self.grid_counts)
        pandas.set_option("display.max_rows", None, "display.max_columns", None)
        pandas.options.display.width = 0
        print(df)

    def calc_open_unopenable(self):
        pass

    def calc_repeat_failed(self):
        pass

    def calc_impossible(self):
        pass

    def calc_not_moving_toward_object(self):
        pass

    def calc_multiple_container_look(self):
        pass

    def set_revisit_grid_size(self, grid_size):
        self.grid_size = grid_size
