import json

import numpy as np
import pandas
# from pandas import DataFrame

# Assume that the entire room space goes from -5 to 5 in X and Z.  If this changes,
# then will need to change this line or read in from scene json file.
SPACE_SIZE = 5.

# Grid Dimension determines how big our grid is for revisiting
GRID_DIMENSION = 0.5


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

        # Output values
        self.revisits = 0

    def calc_revisiting(self):

        # Create the grid
        grid = np.zeros([self.grid_size, self.grid_size])

        steps_list = self.history['steps']

        single_step = steps_list[0]
        loc = single_step['output']['position']
        old_x, old_z = self.get_grid_by_location(loc['x'], loc['z'])

        for single_step in steps_list:
            loc = single_step['output']['position']
            grid_x, grid_z = self.get_grid_by_location(loc['x'], loc['z'])
            # print(f"Step value: {single_step['step']}  Location is {loc}.    Grid loc is {grid_x} {grid_z}")

            # If we did not change grid location (for example, change tilt, rotate, etc), do not count
            if old_x == grid_x and old_z == grid_z:
                continue

            grid[grid_x, grid_z] += 1
            old_x, old_z = grid_x, grid_z

        # Ignore all the grid cells with 1's or 0's, by subtracting 1 and making 0 the minimum.
        grid -= 1
        grid = np.clip(grid, 0, None)
        self.revisits = grid.sum()

        # Use a Pandas Dataframe to print it out
        df = pandas.DataFrame(grid)
        pandas.set_option("display.max_rows", None, "display.max_columns", None)
        pandas.options.display.width = 0
        print(df)

        print(f"Total number of revisits: {self.revisits}")

        pass

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
