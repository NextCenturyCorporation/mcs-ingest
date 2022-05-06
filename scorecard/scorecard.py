#
# Calculate the Scorecard for a particular MCS output JSON file
#
#
import logging
import math
from collections import defaultdict
from operator import itemgetter

import numpy as np
import pandas
# Grid Dimension determines how big our grid is for revisiting
from machine_common_sense.action import MOVE_ACTIONS, Action

from scorecard.scorecard_location_utils import is_on_ramp, up_ramp_or_down

GRID_DIMENSION = 0.5

# Direction limit:  Degrees difference that we allow before we count actors
# as facing in the same direction
DIRECTION_LIMIT = 11

# Minimum timesteps between looking in a container and looking again before
# we count again.  We start counting when AI opens the container, but it
# could be unable to see into the container (on back side), so give it time to
# go around the front
STEPS_BETWEEN_RELOOKS = 15

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

# Amount of distance down that we will use as a limit of a fall.
# If the AI drops that much between moves, then it counts as a fall.
# Ramps have max angle of 45 degrees, so make this bigger than
# the vertical distance going down step on a ramp.
FALL_DISTANCE = -0.3
STEP_CHECK_FALL_OFF = 5

# Minimum amount of vertical change of a ramp.  We need this because
# (for some reason) Unity sometimes changes the vertical (y) value
# even going on level ground, so cannot count y_2 > y_1 as having
# gone up a ramp.
RAMP_MIN_HEIGHT_CHANGE = 0.1

# When we are this close to the ramp base, count it as on the base.
DIST_LIMIT_FROM_BASE = 0.1

DEFAULT_ROOM_DIMENSIONS = {'x': 10, 'y': 3, 'z': 10}


def get_relevant_object(output) -> str:
    """See if there is an object for the current action output"""
    resolved_obj = output.get('resolved_object')
    if resolved_obj is not None and len(resolved_obj) > 0:
        return resolved_obj

    resolved_recept = output.get('resolved_receptacle')
    if resolved_recept is not None and len(resolved_recept) > 0:
        return resolved_recept

    object_id = output.get('objectId')
    if object_id is not None and len(object_id) > 0:
        return object_id

    return ""


def calc_repeat_failed(steps_list: list) -> dict:
    """Calculate repeated failures, so keep track of first
    time a failure occurs, then increment after that.  """

    previously_failed = []
    repeat_failed = 0
    failed_objects = defaultdict(int)

    for step_num, single_step in enumerate(steps_list):
        action = single_step['action']
        output = single_step['output']
        return_status = output['return_status']
        logging.debug(f"{step_num}  {action}  {return_status}")

        if return_status == 'SUCCESSFUL':
            continue

        if return_status == 'OBSTRUCTED':
            continue

        # FAILED means an internal MCS error.  Report and continue
        if return_status == 'FAILED':
            logging.warning(f"Received FAILED for step {step_num}!!!!")
            continue

        # Round floats so we have more accurate key string comparisons.
        position = output['position']
        for axis in ['x', 'y', 'z']:
            if axis in position:
                position[axis] = round(position[axis], 2)

        # Get the id of the object that was used, if any
        obj_id = get_relevant_object(output)

        # Create a unique string identifier for the action and status. This
        # includes the performer's position and rotation (because, if the
        # performer moves between failed actions, we don't count it) and
        # the action's object params (because, if the performer uses the
        # same action on a different object, or the same action with
        # different coords for the same object, we don't count it).
        key = '_'.join([
            action,
            return_status,
            str(position),
            str(single_step['output']['rotation']),
            str(obj_id)
        ])

        # If already failed, then count; otherwise keep track that
        # it failed a first time.
        if key in previously_failed:
            repeat_failed += 1
            failed_objects[str(obj_id)] += 1
            logging.debug(f"Repeated failure {key} : {repeat_failed}")
        else:
            previously_failed.append(key)
            logging.debug(f"First failure: {key} : {repeat_failed}")

    failed_dict = {}
    failed_dict['total_repeat_failed'] = repeat_failed
    failed_dict.update(failed_objects)
    return failed_dict


def minAngDist(a, b):
    """Calculate the difference between two angles in degrees, keeping
    in mind that 0 and 360 are the same.  Also, keep value in range [0-180].
    You cannot just do an abs(a-b).    """
    normDeg = (a - b) % 360
    return min(360 - normDeg, normDeg)


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

    return locs[dists.index(min(dists))] if dists else []


def find_target_loc_by_step(scene, step):
    '''Get the x,z of the target in the step information, if any.
    If it exists, return True and the location;  otherwise,
    return False'''
    try:
        target_info = step["output"]["goal"]["metadata"]["target"]
        target_id = target_info["id"]
        target_pos = target_info["position"]
        x, y, z = itemgetter('x', 'y', 'z')(target_pos)
        return target_id, x, z
    except Exception:
        logging.error(f"No target by step data for scene {scene['name']}")

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

        x_size = scene.get("roomDimensions", DEFAULT_ROOM_DIMENSIONS).get("x")
        z_size = scene.get("roomDimensions", DEFAULT_ROOM_DIMENSIONS).get("z")
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

        self.calc_open_unopenable()
        self.calc_relook()
        self.calc_revisiting()
        self.calc_not_moving_toward_object()
        self.calc_ramp_actions()

        # To be implemented
        # self.calc_attempt_impossible()

        return {
            'repeat_failed': self.repeat_failed,
            'attempt_impossible': self.attempt_impossible,
            'open_unopenable': self.open_unopenable,
            'container_relook': self.relooks,
            'not_moving_toward_object': self.not_moving_toward_object,
            'revisits': self.revisits,
        }

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
        # logging.print_grid()
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
        logging.debug('Starting calculating unopenable')
        steps_list = self.history['steps']

        unopenable = 0
        failed_objects = defaultdict(int)

        for single_step in steps_list:
            step = single_step['step']
            action = single_step['action']
            output = single_step['output']
            if action == 'OpenObject':
                return_status = output['return_status']
                if return_status in ["SUCCESSFUL",
                                     "IS_OPENED_COMPLETELY",
                                     'OUT_OF_REACH']:
                    logging.debug(
                        f"Successful opening of container. Step {step}")
                else:
                    obj_id = get_relevant_object(output)
                    if obj_id != "":
                        failed_objects[obj_id] += 1
                    logging.debug("Unsuccessful opening of object {obj_id} " +
                                  f"Step {step} Status: {return_status}")
                    unopenable += 1

        self.open_unopenable = {}
        self.open_unopenable['total_unopenable_attempts'] = unopenable
        self.open_unopenable.update(failed_objects)
        logging.debug('Ending calculating unopenable')
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

            if action == 'OpenObject':
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

            target_id, target_x, target_z = \
                find_target_loc_by_step(self.scene, single_step)
            logging.debug("Target location at step " +
                          f"{step_num}:  {target_x}  {target_z}")
            if target_id is None:
                return self.not_moving_toward_object

            visible = single_step.get('target_visible')
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

    def calc_ramp_actions(self):
        '''Calculate the number of times that the AI went
        up ramps, failed to go up/down a ramp (went other way),
        and fell off.'''
        logging.debug('Starting calculating ramp actions')
        steps_list = self.history['steps']

        old_position = steps_list[0]['output']['position']
        was_on_ramp = False
        headed_up = False
        orig_y = 0.0
        ramp_actions = {'went_up': 0,
                        'went_down': 0,
                        'went_up_abandoned': 0,
                        'went_down_abandoned': 0,
                        'ramp_fell_off': 0}
        last_ramp_action_step = 0
        last_ramp_action_position = old_position
        last_ramp_action = 'None'

        for single_step in steps_list:
            step = single_step['step']
            action = Action(single_step['action'])
            output = single_step['output']
            return_status = output['return_status']
            logging.debug(f"On step: {step}")

            # Can only go up/down a ramp when actually moving
            if action not in MOVE_ACTIONS:
                logging.debug(f"Not a move {action}")
                continue

            if return_status != "SUCCESSFUL":
                logging.debug(f"Not successful {return_status}")
                continue

            position = output['position']
            now_on_ramp, ramp_rot, ramp_name = self.on_ramp(position)
            logging.debug(f"Whether on ramp:   {now_on_ramp} {ramp_name}")

            # Special case:  We previously thought that we had reached the top
            # or bottom, but we really went over the side and just didn't
            # realize it at the time.  This can occur when the AI goes
            # up the ramp, then goes mostly over the side, but the size
            # of the AI base is such that it didn't drop.
            if (not now_on_ramp) and \
                    (step - last_ramp_action_step) < STEP_CHECK_FALL_OFF:
                if self.fell_off_ramp(last_ramp_action_position, position):
                    ramp_actions[last_ramp_action] -= 1
                    ramp_actions['ramp_fell_off'] += 1
                    last_ramp_action_step = 0
                    continue

            # Case 1:  Unchanged (either on ramp or off ramp)
            if was_on_ramp == now_on_ramp:
                logging.debug("No ramp change")
                old_position = position
                continue

            # Case 2:  started a ramp.
            if now_on_ramp and not was_on_ramp:
                orig_y = old_position['y']
                was_on_ramp = now_on_ramp
                headed_up = up_ramp_or_down(
                    old_position['x'],
                    old_position['z'],
                    position['x'],
                    position['z'],
                    ramp_rot)
                old_position = position
                logging.debug(f"Starting ramp {step} Up:" +
                              f"{headed_up}. Y orig {orig_y}")
                continue

            # Case 3: Exited a ramp!
            # This is the interesting one.  Figure out if
            # we went up, went down, or fell off
            logging.debug("Now off ramp!")
            was_on_ramp = False

            height_change = position['y'] - orig_y

            # See if we successfully completed a ramp going up
            if headed_up and height_change > RAMP_MIN_HEIGHT_CHANGE:
                ramp_actions['went_up'] += 1
                logging.debug("were headed up, now off ramp on top " +
                              f"{step} {ramp_actions['went_up']}")
                old_position = position
                last_ramp_action = 'went_up'
                last_ramp_action_step = step
                last_ramp_action_position = position
                continue

            # If we were going up but didn't end up higher, then we
            # either turned around or fell off
            if headed_up:
                ramp_actions['went_up_abandoned'] += 1
                logging.debug(f"were headed up, abandoned {step}" +
                              f"{ramp_actions['went_up_abandoned']}")
                old_position = position
                continue

            # At this point we know we were going down.  Handle these cases.

            # See if the drop was a lot, meaning fell off
            if self.fell_off_ramp(old_position, position):
                ramp_actions['fell_off_going_down'] += 1
                logging.debug(f"fell off going down {step} " +
                              f"{ramp_actions['ramp_fell_off']}")
                old_position = position
                continue

            # If didn't fall off, but overall height change was a lot,
            # then success
            if height_change < -RAMP_MIN_HEIGHT_CHANGE:
                ramp_actions['went_down'] += 1
                logging.debug("were headed down, now off ramp on bottom " +
                              f"{step} {ramp_actions['went_down']}")
                old_position = position
                last_ramp_action = 'went_down'
                last_ramp_action_step = step
                last_ramp_action_position = position
                continue

            # Last case is they went down, but turned around
            ramp_actions['went_down_abandoned'] += 1
            logging.debug("were headed down, but went back up " +
                          f"{step} {ramp_actions['went_down_abandoned']}")
            old_position = position
            continue

        self.ramp_actions = {}
        self.ramp_actions.update(ramp_actions)
        logging.debug('Ending calculating ramp actions')
        return self.ramp_actions

    def on_ramp(self, position) -> (bool, float, str):
        '''Determine if a position is in a ramp.  Return
        a boolean and, if True, ramp rotation and the ID'''

        for obj in self.scene['objects']:
            if obj['type'] != 'triangle':
                continue

            x = position['x']
            z = position['z']
            if 'shows' in obj and len(obj['shows']) > 0:
                sh = obj['shows'][0]
                pos = sh['position']
                size = sh['scale']
                rot = sh['rotation']['y']
                on_obj = is_on_ramp(
                    x, z,
                    pos['x'], pos['z'],
                    size['x'], size['z'],
                    rot)
                if on_obj:
                    return True, rot, obj['id']
        return False, 0, ""

    def fell_off_ramp(self,
                      old_position,
                      new_position) -> bool:
        # If they dropped a lot, then must have fallen.  This
        # logic might not hold if, in the future, some other
        # action causes them to go down.
        amount_down = new_position['y'] - old_position['y']
        if amount_down < FALL_DISTANCE:
            return True

        # If the above logic does not hold (i.e. other things
        # can cause substantial vertical changes, we might need
        # to calculate whether went over the side of a ramp and
        # dropped.  We can use geometry to see if the movement
        # old->new position intersects with the side of the ramp.
        # However, the logic could be complicated because:
        #   a. AI agent is affected by the ramp when the position is
        #      not technically over the ramp any more
        #   b. the AI agent might not be going straight down the ramp
        #      so might go over the bottom corner of the ramp and
        #      we probably don't want to count that as a 'fall'.

        return False

    def calc_repeat_failed(self):
        """Calculate repeated failures, so keep track of first
        time a failure occurs, then increment after that.  """

        steps_list = self.history['steps']
        self.repeat_failed = calc_repeat_failed(steps_list)
        return self.repeat_failed

    def calc_attempt_impossible(self):
        pass

    def set_revisit_grid_size(self, grid_size):
        self.grid_size = grid_size
