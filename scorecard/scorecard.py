#
# Calculate the Scorecard for a particular MCS output JSON file
#
#
import json

import numpy as np
import pandas

# Assume that the entire room space goes from -5 to 5 in X and Z.  If not,
# then will need to change this line or read in from scene json file.
SPACE_SIZE = 5.

# Grid Dimension determines how big our grid is for revisiting
GRID_DIMENSION = 0.5

# Direction limit:  Degrees difference that we allow before we count actors
# as facing in the same direction
DIRECTION_LIMIT = 11


def minAngDist(a, b):
    """Calculate the difference between two angles in degrees, keeping
    in mind that 0 and 360 are the same.  Also, keep value in range [0-180].
    You cannot just do an abs(a-b).    """
    normDeg = (a - b) % 360
    minAng = min(360 - normDeg, normDeg)
    return minAng


class GridHistory:
    """A history of the times a grid square has been visited"""

    def __init__(self):
        self.stepnums = []
        self.directions = []

    def add(self, stepnum: int, direction: int):
        self.stepnums.append(stepnum)
        self.directions.append(direction)

    def seen_before(self, stepnum: int, direction: int):
        for previous_direction in self.directions:
            diff = minAngDist(previous_direction, direction)
            if diff < DIRECTION_LIMIT:
                return True
        return False

    def any_visits(self):
        size_of_stepnums = len(self.stepnums)
        if size_of_stepnums == 0:
            return False
        return True


class Scorecard:
    """
    Scorecard calculates and holds information on several measures
    of performance for an agent moving in the active tasks.

    Reminder: location in Unity is a left-handed, y-up axis orientation system.
    See:  https://docs.unity3d.com/Manual/class-Transform.html
    So we process (X,Z) locations.
    """

    def __init__(self, json_filepath):
        self.history_file_name = json_filepath
        with open(self.history_file_name) as history_file:
            self.history = json.load(history_file)

        # Size of the grid for calculating revisiting
        self.grid_dimension = GRID_DIMENSION
        self.grid_size = (int)(2 * SPACE_SIZE / self.grid_dimension)

        # Create the grid history and the counts
        self.grid = [[GridHistory() for j in range(self.grid_size)]
                     for i in range(self.grid_size)]
        self.grid_counts = np.zeros([self.grid_size, self.grid_size])

        # Output values
        self.revisits = 0

    def get_revisits(self):
        return self.revisits

    def calc_revisiting(self):

        steps_list = self.history['steps']

        step_num = 0
        single_step = steps_list[0]
        loc = single_step['output']['position']
        old_x, old_z = self.get_grid_by_location(loc['x'], loc['z'])

        previous_revisit = False

        for single_step in steps_list:

            step_num += 1
            loc = single_step['output']['position']
            direction = single_step['output']['rotation']

            grid_x, grid_z = self.get_grid_by_location(loc['x'], loc['z'])
            grid_hist = self.grid[grid_x][grid_z]
            print(f"Step num {step_num}  Location is {loc}.  Dir: " +
                  "{direction}  Grid loc is {grid_x} {grid_z}")

            # ---------------------------------
            # Determine if this is a revisit
            # ---------------------------------
            # If never been there, then not a revisit, and no longer in
            # revisiting mode
            if not grid_hist.any_visits():
                print("never visited")
                grid_hist.add(step_num, direction)
                old_x, old_z = grid_x, grid_z
                previous_revisit = False
                continue

            # If we did not change grid location (for example, change tilt,
            # rotate, etc), do not count
            if old_x == grid_x and old_z == grid_z:
                print("didn't change location")
                old_x, old_z = grid_x, grid_z
                grid_hist.add(step_num, direction)
                continue

            # See if ever been in this direction before
            if not grid_hist.seen_before(step_num, direction):
                print("visited but not this direction")
                grid_hist.add(step_num, direction)
                old_x, old_z = grid_x, grid_z
                previous_revisit = False
                continue

            # If previous step was a revisit, don't mark this one, but
            # still in revisiting mode
            if previous_revisit:
                print("visited and this direction, but in revisiting mode")
                grid_hist.add(step_num, direction)
                old_x, old_z = grid_x, grid_z
                continue

            # At this point, we just moved to a place, we have already been
            # there, we are facing in the same direction as before, and
            # previous_revisit==False (i.e. we are not in revisiting mode)
            # So, we are revisiting
            print("revisiting")
            previous_revisit = True
            self.grid_counts[grid_x, grid_z] += 1
            old_x, old_z = grid_x, grid_z

        self.revisits = self.grid_counts.sum()

        # Debug printing
        self.print_grid()
        print(f"Total number of revisits: {self.revisits}")

        return self.revisits

    def get_grid_by_location(self, x, z):
        """ Given float x,z, determine the int vals for the grid location"""
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
        pandas.set_option("display.max_rows", None,
                          "display.max_columns", None)
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
