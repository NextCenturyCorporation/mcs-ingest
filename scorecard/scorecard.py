#
# Calculate the Scorecard for a particular MCS output JSON file
#
#
import logging
import math
from operator import itemgetter

import numpy as np
import pandas

# Grid Dimension determines how big our grid is for revisiting
GRID_DIMENSION = 0.5

# Direction limit:  Degrees difference that we allow before we count actors
# as facing in the same direction
DIRECTION_LIMIT = 11

# Minimum timesteps between looking in a container and looking again before
# we count again
STEPS_BETWEEN_RELOOKS = 10

# Min distance between 'look' locations such that we count them as looking
# in the same container
DIST_BETWEEN_RELOOKS = 0.4

# Min angle of tilt looking down that counts as an agent looking into a
# container
MIN_TILT_LOOK_DOWN = 30

# Min number of times in a row that the target has to be visible for us
# to count it as seen by the agent, because the target can be 'visible'
# but only in the corner for a single frame.
SEEN_COUNT_MIN = 4

# How many steps required before the agent has to have moved toward the
# target?  If there is an object between the agent and the target
# this gives it time to turn move to the side (about 15 steps), turn (9),
# and move towards it (15).  So about 30 steps.
STEPS_NOT_MOVED_TOWARD_LIMIT = 30


def minAngDist(a, b):
    """Calculate the difference between two angles in degrees, keeping
    in mind that 0 and 360 are the same.  Also, keep value in range [0-180].
    You cannot just do an abs(a-b).    """
    normDeg = (a - b) % 360
    minAng = min(360 - normDeg, normDeg)
    return minAng


def get_lookpoint(x, y, z, rot, tilt):
    # Given a location of agent, determine where they are looking.
    # Make sure that tilt is within a good range; if agent is not
    # looking down, return current loc.
    # Reminder:  Unity is left-handed, y-up, so floor is (X,Z) plane
    if tilt > 90 or tilt <= 0:
        logging.warning(f"Not computing dist, tilt is {tilt}")
        return x, z

    # Ground dist from current location is fn of height (y) and tilt angle
    dist = y * math.tan(math.radians(90 - tilt))

    # Distance in x,z depends on rotation and total distance on ground
    dx = dist * math.cos(math.radians(90 - rot))
    dz = dist * math.sin(math.radians(90 - rot))

    logging.debug(f"xyz ({x:0.3f} {y:0.3f} {z:0.3f})" +
                  f" tilt {tilt:0.3f} rot {rot:0.3f}")
    logging.debug(f"dist is {dist:0.3f}.  dx,dz {dx:0.3f} {dz:0.3f}")
    logging.debug(f"looking point: {(x + dx):0.3f}  {(z + dz):0.3f}")
    return (x + dx), (z + dz)


def calc_viewpoint(step_metadata):
    # Get location, remember coordinate system is left-handed, y-up
    x, y, z = itemgetter('x', 'y', 'z')(step_metadata['output']['position'])
    rot = step_metadata['output']['rotation']
    tilt = step_metadata['output']['head_tilt']
    return get_lookpoint(x, y, z, rot, tilt)


def find_closest_container(x, z, scene):
    dists = []
    locs = []
    for room_object in scene['objects']:
        # Not all objects have openable, so make sure it is a key
        if 'openable' not in room_object or not room_object['openable']:
            continue

        type = room_object['type']
        cx = room_object['shows'][0]['position']['x']
        cz = room_object['shows'][0]['position']['z']
        dist = math.dist((x, z), (cx, cz))
        dists.append(dist)
        locs.append({'type': type, 'x': cx, 'z': cz})

    return locs[dists.index(min(dists))]


def find_target_location(scene):
    '''Get the x,z of the target, if any.  If it exists, return
    True and the location;  otherwise, return False'''
    try:
        target_id = scene["goal"]["metadata"]["target"]["id"]
        for possible_target in scene["objects"]:
            test_id = possible_target["id"]
            if test_id == target_id:
                pos = possible_target['shows'][0]['position']
                x, y, z = itemgetter('x', 'y', 'z')(pos)
                return target_id, x, z
        logging.warning(f"Target is supposed to be {target_id} but not found!")
    except Exception:
        logging.debug(f"No target in scene {scene['name']}")

    return None, 0, 0


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
        """Has this grid cell ever been visited"""
        return len(self.stepnums) > 0


class Scorecard:
    """
    Scorecard calculates and holds information on several measures
    of performance for an agent moving in the active tasks.

    Reminder: location in Unity is a left-handed, y-up axis orientation system.
    See:  https://docs.unity3d.com/Manual/class-Transform.html
    So we process (X,Z) locations.
    """

    def __init__(self, history: dict, scene: dict):

        self.history = history
        self.scene = scene

        x_size = scene.get("roomDimensions").get("x")
        z_size = scene.get("roomDimensions").get("z")
        self.space_size = 2 * max(x_size, z_size)

        # Size of the grid for calculating revisiting
        self.grid_dimension = GRID_DIMENSION
        self.grid_size = (int)(2 * self.space_size / self.grid_dimension)

        # Create the grid history and the counts
        self.grid = [[GridHistory() for j in range(self.grid_size)]
                     for i in range(self.grid_size)]
        self.grid_counts = np.zeros([self.grid_size, self.grid_size])

        # Output values
        self.revisits = 0
        self.repeat_failed = 0
        self.attempt_impossible = 0
        self.open_unopenable = 0
        self.relooks = 0
        self.not_moving_toward_object = 0

    def score_all(self) -> dict:
        self.calc_repeat_failed()
        self.calc_attempt_impossible()
        self.calc_open_unopenable()
        self.calc_relook()
        self.calc_revisiting()
        self.calc_not_moving_toward_object()

        scorecard_vals = {}
        scorecard_vals["repeat_failed"] = self.repeat_failed
        scorecard_vals["attempt_impossible"] = self.attempt_impossible
        scorecard_vals["open_unopenable"] = self.open_unopenable
        scorecard_vals["multiple_container_look"] = self.relooks
        scorecard_vals["not_moving_toward_object"] = \
            self.not_moving_toward_object
        scorecard_vals["revisits"] = self.revisits

        return scorecard_vals

    def get_revisits(self):
        return self.revisits

    def get_unopenable(self):
        return self.open_unopenable

    def get_relooks(self):
        return self.relooks

    def get_not_moving_towards(self):
        return self.not_moving_toward_object

    def get_repeat_failed(self):
        return self.repeat_failed

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
            logging.debug(f"Step num {step_num}  Location is {loc}.  Dir: " +
                          f"{direction}  Grid loc is {grid_x} {grid_z}")

            # ---------------------------------
            # Determine if this is a revisit
            # ---------------------------------
            # If never been there, then not a revisit, and no longer in
            # revisiting mode
            if not grid_hist.any_visits():
                logging.debug("never visited")
                grid_hist.add(step_num, direction)
                old_x, old_z = grid_x, grid_z
                previous_revisit = False
                continue

            # If we did not change grid location (for example, change tilt,
            # rotate, etc), do not count
            if old_x == grid_x and old_z == grid_z:
                logging.debug("didn't change location")
                old_x, old_z = grid_x, grid_z
                grid_hist.add(step_num, direction)
                continue

            # See if ever been in this direction before
            if not grid_hist.seen_before(step_num, direction):
                logging.debug("visited but not this direction")
                grid_hist.add(step_num, direction)
                old_x, old_z = grid_x, grid_z
                previous_revisit = False
                continue

            # If previous step was a revisit, don't mark this one, but
            # still in revisiting mode
            if previous_revisit:
                logging.debug("visited / this direction, but in revisit mode")
                grid_hist.add(step_num, direction)
                old_x, old_z = grid_x, grid_z
                continue

            # At this point, we just moved to a place, we have already been
            # there, we are facing in the same direction as before, and
            # previous_revisit==False (i.e. we are not in revisiting mode)
            # So, we are revisiting
            logging.debug("revisiting")
            previous_revisit = True
            self.grid_counts[grid_x, grid_z] += 1
            old_x, old_z = grid_x, grid_z

        self.revisits = int(self.grid_counts.sum())

        # Debug printing
        # logging.debug_grid()
        logging.debug(f"Total number of revisits: {self.revisits}")

        return self.revisits

    def get_grid_by_location(self, x, z):
        """ Given float x,z, determine the int vals for the grid location"""
        grid_x = (int)((self.space_size + x) / self.grid_dimension)
        grid_z = (int)((self.space_size + z) / self.grid_dimension)

        if grid_x < 0 or grid_x > self.grid_size - 1:
            logging.warning(
                f"Problem with x loc {x}.  got grid loc {grid_x}.  " +
                "dim {self.grid_dimension} grid size {self.grid_size}")
        if grid_z < 0 or grid_z > self.grid_size - 1:
            logging.warning(
                f"Problem with y loc {z}.  got grid loc {grid_z}.  " +
                "dim {self.grid_dimension} grid size {self.grid_size}")
        return (grid_x, grid_z)

    def print_grid(self):
        # Use a Pandas Dataframe to print it out
        df = pandas.DataFrame(self.grid_counts)
        pandas.set_option("display.max_rows", None,
                          "display.max_columns", None)
        pandas.options.display.width = 0
        logging.debug(df)

    def calc_open_unopenable(self):
        ''' Determine the number of times that the agent tried to
        open an unopenable object.  '''
        steps_list = self.history['steps']

        self.open_unopenable = 0

        for step_num, single_step in enumerate(steps_list):
            action = single_step['action']
            return_status = single_step['output']['return_status']
            if action == 'MCSOpenObject':
                if return_status in ["SUCCESSFUL",
                                     "IS_OPENED_COMPLETELY",
                                     'OUT_OF_REACH']:
                    logging.debug("Successful opening of container")
                else:
                    logging.debug("Unsuccessful opening of container")
                    self.open_unopenable += 1

        return self.open_unopenable

    def calc_relook(self):
        ''' Determine the number of times that the agent relooked into a
        container.  See readme for algorithm.'''

        # Objects to keep track of times that the agent has looked
        # in a container.
        looked_at_containers = []
        last_look_time = -10
        still_looking = False
        self.relooks = 0

        steps_list = self.history['steps']
        for step_num, single_step in enumerate(steps_list):

            # If we had a relook recently, ignore
            if abs(step_num - last_look_time) < STEPS_BETWEEN_RELOOKS:
                logging.debug(f"Skip since too close to last look {step_num}")
                continue

            # If not looking down, then it doesn't count
            tilt = single_step['output']['head_tilt']
            if tilt < MIN_TILT_LOOK_DOWN:
                logging.debug(f"Skip since head tilt to low {tilt}")
                continue

            action = single_step['action']
            return_status = single_step['output']['return_status']
            x, z = calc_viewpoint(single_step)

            if action == 'MCSOpenObject':
                logging.debug("tried to open container")
                container = find_closest_container(x, z, self.scene)

                # Most return_status should be treated like open did not happen
                # happened, but what if too far away or obstructed?
                if return_status == "SUCCESSFUL":
                    logging.debug(" successful ")
                    # Since agent just opened it, not be on the list
                    looked_at_containers.append(container)
                    last_look_time = step_num
                    still_looking = True
                    continue

                elif return_status == "IS_OPENED_COMPLETELY":
                    logging.debug(" already open ")
                    # Since agent already looked at it, must be a relook
                    last_look_time = step_num
                    self.relooks += 1
                    still_looking = True
                    continue

                else:
                    logging.debug(f" something else {return_status} ")

            # determine if this container has been looked at before
            for container_look in looked_at_containers:
                cx = container_look['x']
                cz = container_look['z']

                # Find distance between
                dist = math.dist((x, z), (cx, cz))
                logging.debug(f" looking at {x} {z}  closest: {cx} {cz} " +
                              f"   dist {dist}  still looking {still_looking}")
                if dist < DIST_BETWEEN_RELOOKS and not still_looking:
                    logging.debug("increasing by 1 ")
                    last_look_time = step_num
                    self.relooks += 1
                    continue
                if dist > DIST_BETWEEN_RELOOKS:
                    still_looking = False

        return self.relooks

    def calc_not_moving_toward_object(self):
        """Calculate number of times that the agent
        did not move toward the target"""

        self.not_moving_toward_object = 0

        target_id, target_x, target_z = find_target_location(self.scene)
        logging.debug(f"Target location:  {target_x}  {target_z}")
        if target_id is None:
            return self.not_moving_toward_object

        seen_count = -1
        steps_not_moving_towards = 0
        min_dist = float('inf')

        steps_list = self.history['steps']
        for step_num, single_step in enumerate(steps_list):

            # Do not count non-motion actions, like PASS and TURN
            action = single_step['action']
            if action not in ['MoveAhead', 'MoveBack',
                              'MoveLeft', 'MoveRight']:
                continue

            visible = single_step['target_visible']
            pos = single_step['output']['position']
            x, y, z = itemgetter('x', 'y', 'z')(pos)
            current_dist = math.dist((x, z), (target_x, target_z))
            logging.debug(f"xyz:   {x} {y} {z}")

            # If first time that we have seen the target, start counter
            if seen_count == -1 and visible:
                logging.debug(f"-- First visible {step_num} --")
                seen_count = 1
                steps_not_moving_towards = 0
                continue

            # If the counter is less than the minimum needed and still visible,
            # increase the count.   If not visible, reset counting
            if seen_count < SEEN_COUNT_MIN:
                if visible:
                    min_dist = current_dist
                    seen_count += 1
                    steps_not_moving_towards = 0
                    logging.debug(f"-- visible again {step_num} " +
                                  f"count: {seen_count}  " +
                                  f"dist: {min_dist} --")
                else:
                    seen_count = -1
                    min_dist = -1
                    logging.debug(f"-- not seen at {step_num} reset --")
                continue

            # At this point, target has been seen enough times that we should
            # be moving towards it.  Over time we should get closer and closer
            if current_dist < min_dist:
                min_dist = current_dist
                steps_not_moving_towards = 0
                logging.debug(f"-- moved towards at {step_num} " +
                              f"current_dist: {current_dist} --")
                continue

            # We did not move closer, so increment the counter that keeps
            # track of number of steps
            steps_not_moving_towards += 1
            logging.debug(f"-- did not move towards {step_num} " +
                          f"current_dist: {current_dist}  " +
                          f"count: {steps_not_moving_towards} --")

            # If we have gone enough moves and haven't gotten closer, then
            # increment overall counter and reset
            if steps_not_moving_towards > STEPS_NOT_MOVED_TOWARD_LIMIT:
                self.not_moving_toward_object += 1
                logging.debug(f"-- hit limit {steps_not_moving_towards} " +
                              f"count: {self.not_moving_toward_object} --")
                seen_count = -1
                steps_not_moving_towards = 0

        return self.not_moving_toward_object

    def calc_repeat_failed(self):
        """Calculate repeated failures, so keep track of first
        time a failure occurs, then increment after that.  """

        previously_failed = []
        self.repeat_failed = 0

        steps_list = self.history['steps']
        for step_num, single_step in enumerate(steps_list):
            action = single_step['action']
            return_status = single_step['output']['return_status']
            logging.debug(f"{step_num}  {action}  {return_status}")

            if return_status == 'SUCCESSFUL':
                continue

            if return_status == 'OBSTRUCTED':
                continue

            # FAILED means an internal MCS error.  Report and continue
            if return_status == 'FAILED':
                logging.warning(f"Received FAILED for step {step_num}!!!!")
                continue

            # If already failed, then count; otherwise keep track that
            # it failed a first time.
            key = action + return_status
            if key in previously_failed:
                self.repeat_failed += 1
                logging.debug(f"Repeated failure {key} : {self.repeat_failed}")
            else:
                previously_failed.append(key)
                logging.debug(f"First failure: {key} : {self.repeat_failed}")

        return self.repeat_failed

    def calc_attempt_impossible(self):
        pass

    def set_revisit_grid_size(self, grid_size):
        self.grid_size = grid_size
