#
# Calculate the Scorecard for a particular MCS output JSON file
#
#
import logging
import math
from collections import defaultdict
from operator import itemgetter
from typing import Dict, List

import numpy as np
import pandas

from shapely.geometry import Point, LineString, Polygon

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

PATH_KEY='path'
ALTERNATE_PATH_KEY='slowPath'
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

PERFORMER_WIDTH = 0.25
PERFORMER_HEIGHT = 0.762

MULTI_RETRIEVAL = "multi retrieval"


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
        logging.warning(f"No target by step data for scene {scene['name']}")

    return None, 0, 0

def find_shell_game_container_start_end(container):
    lanes = { -1.5: 1, -0.75: 2, 0: 3, 0.75: 4, 1.5: 5 }
    start = str(lanes[container['position_x']])
    end = str(lanes[container['position_x']])

    horizontal_move = container.get('moves')
    if not horizontal_move:
        return start + ' to ' + end
    move_per_step = horizontal_move[1]['vector']['x']
    steps = horizontal_move[1]['stepEnd'] - horizontal_move[1]['stepBegin'] + 1
    distance = move_per_step * steps

    end = str(lanes[container['position_x'] + distance])
    return start + ' to ' + end

def is_obj_target(scene, obj_id):

    # if not interactive, return
    if scene["goal"]["sceneInfo"]["primaryType"] != "interactive":
        return False

    if(scene["goal"]["sceneInfo"]["secondaryType"] ==
                MULTI_RETRIEVAL):
        for target in scene["goal"]["metadata"]["targets"]:
            if(target['id'] == obj_id):
                return True
    else:
        target_obj = scene["goal"]["metadata"]["target"]
        if(target_obj['id'] == obj_id):
            return True


    return False

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
        self.is_fastest_path = None
        self.ramp_actions = None
        self.tool_usage = None
        self.correct_platform_side = None
        self.correct_door_opened = None
        self.pickup_non_target = False
        self.pickup_not_pickupable = 0
        self.interact_with_non_agent = 0
        self.interact_with_agent = 0
        self.number_of_rewards_achieved = None
        self.stepped_in_lava = None

    def score_all(self) -> dict:
        self.calc_repeat_failed()
        self.calc_open_unopenable()
        self.calc_relook()
        self.calc_revisiting()
        self.calc_not_moving_toward_object()
        self.calc_fastest_path()
        self.calc_ramp_actions()
        self.calc_tool_usage()
        self.calc_correct_platform_side()
        self.calc_correct_door_opened()
        self.calc_pickup_non_target()
        self.calc_pickup_not_pickupable()
        self.calc_agent_interactions()
        self.calc_walked_into_structures()
        self.calc_num_rewards_achieved()
        self.calc_imitation_order_containers_are_opened_colors()
        self.calc_set_rotation()
        self.calc_shell_game()
        self.calc_door_opened_side()
        self.calc_interacted_with_blob_first()
        self.calc_stepped_in_lava()

        # To be implemented
        # self.calc_attempt_impossible()

        return {
            'repeat_failed': self.repeat_failed,
            'attempt_impossible': self.attempt_impossible,
            'correct_door_opened': self.correct_door_opened,
            'correct_platform_side': self.correct_platform_side,
            'open_unopenable': self.open_unopenable,
            'container_relook': self.relooks,
            'not_moving_toward_object': self.not_moving_toward_object,
            'revisits': self.revisits,
            'fastest_path': self.is_fastest_path,
            'ramp_actions': self.ramp_actions,
            'tool_usage': self.tool_usage,
            'pickup_non_target': self.pickup_non_target,
            'pickup_not_pickupable': self.pickup_not_pickupable,
            'interact_with_non_agent': self.interact_with_non_agent,
            'walked_into_structures': self.walked_into_structures,
            'interact_with_agent': self.interact_with_agent,
            'number_of_rewards_achieved': self.number_of_rewards_achieved,
            'order_containers_are_opened_colors': self.order_containers_are_opened_colors,
            'set_rotation_opened_container_position_absolute': self.set_rotation_opened_container_position_absolute,
            'set_rotation_opened_container_position_relative_to_baited': self.set_rotation_opened_container_position_relative_to_baited,
            'shell_game_opened_container_position_relative_to_baited': self.shell_game_opened_container_position_relative_to_baited,
            'shell_game_opened_container': self.shell_game_opened_container,
            'door_opened_side': self.door_opened_side,
            'interacted_with_blob_first': self.interacted_with_blob_first,
            'stepped_in_lava': self.stepped_in_lava
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

    def get_tool_usage(self):
        return self.tool_usage

    def get_interact_with_non_agent(self):
        return self.interact_with_non_agent

    def get_interact_with_agent(self):
        return self.interact_with_agent
    
    def get_pickup_non_target(self):
        return self.pickup_non_target

    def get_pickup_not_pickupable(self):
        return self.pickup_not_pickupable

    def get_walked_into_structures(self):
        return self.walked_into_structures

    def get_number_of_rewards_achieved(self):
        return self.number_of_rewards_achieved

    def get_imitation_order_containers_are_opened(self):
        return self.order_containers_are_opened_colors

    def get_set_rotation_opened_container_position_absolute(self): 
        return self.set_rotation_opened_container_position_absolute

    def get_set_rotation_opened_container_position_relative_to_baited(self): 
        return self.set_rotation_opened_container_position_relative_to_baited

    def get_shell_game_opened_container_position_relative_to_baited(self):
        return self.shell_game_opened_container_position_relative_to_baited

    def get_shell_game_opened_container(self):
        return self.shell_game_opened_container

    def get_door_opened_side(self):
        return self.door_opened_side

    def get_interacted_with_blob_first(self):
        return self.interacted_with_blob_first

    def get_correct_platform_side(self):
        return self.correct_platform_side

    def get_correct_door_opened(self):
        return self.correct_door_opened

    def get_stepped_in_lava(self):
        return self.stepped_in_lava

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

        if(self.scene["goal"]["sceneInfo"]["secondaryType"] ==
                MULTI_RETRIEVAL):
            return 0

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
        last_ramp_action = None

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
            if last_ramp_action is not None and \
                    (not now_on_ramp) and \
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
                ramp_actions['ramp_fell_off'] += 1
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

    def calc_tool_usage(self):
        """Calculate the torques, push, pulls, moves. Also includes
        calculations for multi tool specific scorecard values."""
        steps_list = self.history['steps']

        tool_usage = defaultdict(int)

        is_multi_tool = (self.scene['goal']['sceneInfo'].get('tertiaryType') and
                    self.scene['goal']['sceneInfo']['tertiaryType'] == "multi tool use")
        unique_tools = set()
        is_hooked_rotated = False
        is_straight_rotated = False

        for single_step in steps_list:
            action = single_step['action']
            output = single_step['output']
            return_status = output['return_status']

            if action in ['MoveObject', 'PushObject',
                          'PullObject', 'RotateObject',
                          'TorqueObject']:
                resolved_obj = get_relevant_object(output)
                if resolved_obj.startswith('tool') and return_status == 'SUCCESSFUL':
                    tool_usage[action] += 1

                    if is_multi_tool:
                        unique_tools.add(resolved_obj)

                        if action in ['RotateObject', 'TorqueObject']:
                            tool_object = [obj for obj in self.scene['objects']
                                if obj['id'] == resolved_obj]
                            if(len(tool_object) > 0):
                                if(is_straight_rotated == False and tool_object[0]['type'].startswith('tool_rect')):
                                    is_straight_rotated = True
                                if(is_hooked_rotated == False and (tool_object[0]['type'].startswith('tool_hooked') or
                                                                   tool_object[0]['type'].startswith('tool_isosceles'))):
                                    is_hooked_rotated = True

                else:
                    tool_usage[action + '_failed'] += 1

        if(is_multi_tool):
            tool_usage["total_tools_used"] = len(unique_tools)
            tool_usage["is_hooked_rotated"] = is_hooked_rotated
            tool_usage["is_straight_rotated"] = is_straight_rotated

        self.tool_usage = tool_usage
        return self.tool_usage

    def calc_correct_platform_side(self):
        '''Determine if the ai agent went on the correct
        side of the platform.

        Assumptions for calculating the correct platform side:
            - performer position Y drops by a value greater than 0.4 when
              platform is chosen
            - scene has "targetSide" tag set to either "left" or "right" (the
              case where targetSide is "center" isn't covered here/is typically
              handled instead by correct_door_opened)
            - correct performer position X should match targetSide, with
              negative X being "left" and positive X being "right"
        '''

        # Does this scene have a clear targetSide? If not, return
        # correct_platform_side (currently set to None).
        goal = self.scene.get('goal')
        if ('sceneInfo' in goal and 'targetSide' in goal['sceneInfo'] and
                goal['sceneInfo']['targetSide'] in ['left', 'right']):
            target_side = goal['sceneInfo']['targetSide']
        elif (
            'sceneInfo' in goal and
            'toolChoiceValidSide' in goal['sceneInfo'] and
            goal['sceneInfo']['toolChoiceValidSide'] in ['left', 'right']
        ):
            # Support Eval 6 Tool Choice scenes.
            target_side = goal['sceneInfo']['toolChoiceValidSide']
        elif (
            'sceneInfo' in goal and 'relation' in goal['sceneInfo'] and
            goal['sceneInfo']['relation'] in ['sameSide', 'oppositeSide'] and
            'type' in goal['sceneInfo'] and
            goal['sceneInfo']['type'] in ['collision', 'noCollision']
        ):

            # Support for Eval 6 Interactive Collisions
            throwing_device = [obj for obj in self.scene['objects']
                    if obj['id'].startswith('throwing_device_')]

            # if for whatever reason, we can't find the
            # throwing device, return
            if len(throwing_device) == 0:
                return self.correct_platform_side

            relation = goal['sceneInfo']['relation']
            collision = goal['sceneInfo']['type']
            x_pos = throwing_device[0]['shows'][0]['position']['x']

            is_target_same_side = relation == 'sameSide' and collision == 'noCollision'
            if is_target_same_side:
                target_side = 'left' if x_pos < 0 else 'right'
            else:
                target_side = 'right' if x_pos < 0 else 'left'
        elif (
            'sceneInfo' in goal and 'finalRewardLocation' in goal['sceneInfo'] and
            goal['sceneInfo']['finalRewardLocation'] in ['left', 'right']):

            # Support for Eval 6 Trajectory Scenes
            finalRewardLoc = goal['sceneInfo']['finalRewardLocation']

            target_side = 'left' if finalRewardLoc == 'left' else 'right'
        else:
            return self.correct_platform_side

        # If they never leave the platform, mark it as failed.
        self.correct_platform_side = False

        steps_list = self.history['steps']
        output = steps_list[0]['output']
        old_y = output['position']['y']
        for single_step in steps_list:
            output = single_step['output']
            new_y = output['position']['y']
            # This could probably also be "new_y == PERFORMER_HEIGHT" but the
            # current code seems better at avoiding floating point errors.
            # This number represents the height of the platform.
            if new_y <= (old_y - 0.4):
                x = output['position']['x']
                if x < 0:
                    self.correct_platform_side = (target_side == 'left')
                elif x > 0:
                    self.correct_platform_side = (target_side == 'right')
            old_y = new_y

        return self.correct_platform_side


    def calc_correct_door_opened(self):
        """
        Determine if the ai agent went through the correct door

        Assumptions for calculating the correct door:
            - OpenObject was called successfully on a door object
            - door object IDs begin with "door_"
            - door positions are either positive X, negative X, or zero
            - scene has "correctDoor" tag set to either "left", "right", or 
              "center"

        """

        # Does this scene have a correctDoor? If not, return
        # correct_door_opened (currently set to None).
        goal = self.scene.get('goal')
        if ('sceneInfo' in goal and 'correctDoor' in goal['sceneInfo'] and
                goal['sceneInfo']['correctDoor'] is not None):
            correct_door = goal['sceneInfo']['correctDoor']
        elif (
            'sceneInfo' in goal and 'relation' in goal['sceneInfo'] and
            goal['sceneInfo']['relation'] in ['sameSide', 'oppositeSide'] and
            'type' in goal['sceneInfo'] and
            goal['sceneInfo']['type'] in ['collision', 'noCollision']
        ):
            # Support for Eval 6 Interactive Collisions
            throwing_device = [obj for obj in self.scene['objects']
                    if obj['id'].startswith('throwing_device_')]

            # if for whatever reason, we can't find the
            # throwing device, return
            if len(throwing_device) == 0:
                return self.correct_door_opened

            relation = goal['sceneInfo']['relation']
            collision = goal['sceneInfo']['type']
            x_pos = throwing_device[0]['shows'][0]['position']['x']

            is_target_same_side = relation == 'sameSide' and collision == 'noCollision'
            if is_target_same_side:
                correct_door = 'left' if x_pos < 0 else 'right'
            else:
                correct_door = 'right' if x_pos < 0 else 'left'

        elif (
            'sceneInfo' in goal and 'finalRewardLocation' in goal['sceneInfo'] and
            goal['sceneInfo']['finalRewardLocation'] in ['left', 'right']):

            # Support for Eval 6 Trajectory Scenes
            finalRewardLoc = goal['sceneInfo']['finalRewardLocation']

            correct_door = 'left' if finalRewardLoc == 'left' else 'right'
        else:
            return self.correct_door_opened

        steps_list = self.history['steps']
        output = steps_list[0]['output']

        for single_step in steps_list:
            action = single_step['action']
            output = single_step['output']
            return_status = output['return_status']

            if action in ['OpenObject']:
                obj_id = get_relevant_object(output)

                if 'door_' in obj_id and return_status == 'SUCCESSFUL':
                    for obj in self.scene['objects']:
                        if obj['id'] == obj_id:
                            break

                    if 'shows' in obj and len(obj['shows']) > 0:
                        door_x_pos = obj['shows'][0]['position']['x']
                        if door_x_pos == 0 and correct_door == 'center':
                            self.correct_door_opened = True
                        elif door_x_pos < 0 and correct_door == 'left':
                            self.correct_door_opened = True
                        elif door_x_pos > 0 and correct_door == 'right':
                            self.correct_door_opened = True
                        else:
                            self.correct_door_opened = False

        return self.correct_door_opened

    def calc_attempt_impossible(self):
        pass

    def set_revisit_grid_size(self, grid_size):
        self.grid_size = grid_size

    def calc_fastest_path(self):
        if not self.scene.get(PATH_KEY) or not self.scene.get(ALTERNATE_PATH_KEY):
            return
        paths = [self.scene[PATH_KEY], self.scene[ALTERNATE_PATH_KEY]]
        steps_list = self.history['steps']
        
        distances=[]
        
        start_pos = self.scene['performerStart']['position']
        
        for path in paths:
            distance=0
            for idx, single_step in enumerate(steps_list):
                position=single_step['output']['position']
                single_dist = self.get_distance_from_path(start_pos, position, path)
                distance+=single_dist
            distances.append(distance)
        
        self.is_fastest_path = distances[0] == min(distances)
            
    def get_distance_from_path(self, start_pos: Dict[str, float],position: Dict[str, float], path: List[Dict[str, float]]):
        p1 = start_pos
        p1 = Point((start_pos['x'], start_pos['z']))
        pos = Point((position['x'], position['z']))
        dist = 10000000
        for pnt in path:
            p2 = Point((pnt['x'], pnt['z']))
            
            line = LineString([p1, p2])
            
            dist=min(pos.distance(line),dist)
            p1 = p2
        return dist
    
    def calc_pickup_non_target(self):
        """
        Calculate whether the performer agent picked up a non-target
        soccer ball. Will ignore ambiguous multi-retrieval scenes.
        """
        if (
            self.scene['goal']['category'] == MULTI_RETRIEVAL and
            self.scene['goal'].get('sceneInfo', {}).get('ambiguous')
        ):
            return False
        pickup_non_target = False
        target_list = []
        if 'metadata' in self.scene['goal']:
            if 'target' in self.scene['goal']['metadata']:
                target_list = [self.scene['goal']['metadata']['target']]
            if 'targets' in self.scene['goal']['metadata']:
                target_list = self.scene['goal']['metadata']['targets']
        # Identify all the target ID(s) in the scene file
        target_list = [target['id'] for target in target_list]
        # Identify the soccer ball ID(s) in the scene file
        soccer_ball_list = [
            instance['id'] for instance in self.scene['objects']
            if instance['type'] == 'soccer_ball'
        ]
        if target_list and soccer_ball_list:
            for step_data in self.history['steps']:
                # Identify a successful pickup
                if (
                    step_data['action'] == 'PickupObject' and
                    step_data['output']['return_status'] == "SUCCESSFUL"
                ):
                    # Use "get" for backwards compatibility with old histories
                    resolved_id = step_data['output'].get('resolved_object')
                    if (
                        resolved_id and
                        resolved_id in soccer_ball_list and
                        resolved_id not in target_list
                    ):
                        pickup_non_target = True
        self.pickup_non_target = pickup_non_target
        return self.pickup_non_target

    def calc_pickup_not_pickupable(self):
        ''' 
        Determine the number of times that the performer tried to
        pickup an object than cannot be picked up:
        Agents, Blobs, Floors, Walls, Platforms, Platform Lips, Ramps,
        Static objects (sofas, chairs, etc..), Tools, Walls
        '''
        steps_list = self.history['steps']
        not_pickupable = 0
        for single_step in steps_list:
            action = single_step['action']
            output = single_step['output']
            if action == 'PickupObject' and \
                output['return_status'] == "NOT_PICKUPABLE":
                not_pickupable += 1

        self.pickup_not_pickupable = not_pickupable
        return self.pickup_not_pickupable

    def calc_agent_interactions(self):
        ''' 
        Determine the number of times that the performer tried to
        interact with a non agent when in distance of the object.
        '''
        steps_list = self.history['steps']
        interact_with_non_agent = 0
        interact_with_agent = 0

        agents = [obj['id'] for obj in self.scene['objects']
            if obj['type'].startswith('agent_')]
        for single_step in steps_list:
            action = single_step['action']
            output = single_step['output']
            if (action == 'InteractWithAgent'):
                resolved_obj = output['resolved_object']
                if resolved_obj != '' and resolved_obj not in agents:
                    interact_with_non_agent += 1
                if resolved_obj != '' and resolved_obj in agents and (
                        output['return_status'] == "SUCCESSFUL"):
                    interact_with_agent += 1

        self.interact_with_non_agent = interact_with_non_agent
        self.interact_with_agent = interact_with_agent
        return self.interact_with_non_agent

    def get_min_max_bounding_box_coords(self, bounding_box, key):
        minimum = bounding_box[0][key]
        maximum = bounding_box[0][key]
        for i in range(1, len(bounding_box)):
            value = bounding_box[i][key]
            minimum = min(value, minimum)
            maximum = max(value, maximum)
        return (minimum, maximum)

    def point_is_inside_bounding_box(self, position, bounding_box):
        minimum_y, maximum_y = self.get_min_max_bounding_box_coords(bounding_box, 'y')
        """
        Small buffer otherwise the performer will be detected
        inside the object it's standing on.
        """
        buffer = 0.01
        above = position['y'] - PERFORMER_HEIGHT + buffer > maximum_y
        below = position['y'] - buffer < minimum_y
        if not above and not below:
            minimum_x, maximum_x = self.get_min_max_bounding_box_coords(bounding_box, 'x')
            minimum_z, maximum_z = self.get_min_max_bounding_box_coords(bounding_box, 'z')
            performer_center = Point(position['x'], position['z'])
            performer_bounds = performer_center.buffer(PERFORMER_WIDTH)
            box = [(minimum_x, minimum_z), (minimum_x, maximum_z),
                    (maximum_x, maximum_z), (maximum_x, minimum_z)]
            bb = Polygon(box)
            obstructed_by_this_object = performer_bounds.intersects(bb)
            if obstructed_by_this_object:
                return obstructed_by_this_object
        return False

    def point_is_outside_room_dimensions(self, position, room_dimensions):
        x_room_half_width = room_dimensions['x'] / 2
        z_room_half_width = room_dimensions['z'] / 2
        x = position['x']
        z = position['z']
        beyond_max_x = x + PERFORMER_WIDTH >= x_room_half_width
        beyond_min_x = x - PERFORMER_WIDTH <= -x_room_half_width
        beyond_max_z = z + PERFORMER_WIDTH >= z_room_half_width
        beyond_min_z = z - PERFORMER_WIDTH <= -z_room_half_width
        obs = beyond_max_x or beyond_min_x or beyond_max_z or beyond_min_z
        id = ('room_wall_x+' if beyond_max_x else
                'room_wall_x-' if beyond_min_x else
                'room_wall_z+' if beyond_max_z else
                'room_wall_z-')
        return obs, id

    def get_performer_target_point_based_on_direction(
        self, position, rotation, action):
        move_magnitude = 0.1
        direction = (-90 if action == "MoveLeft" else 90 if action == "MoveRight" 
                    else 180 if action == "MoveBack" else 0)
        x_vector = math.sin(math.radians(rotation + direction)) * move_magnitude
        z_vector = math.cos(math.radians(rotation + direction)) * move_magnitude
        target_x = position['x'] + x_vector
        target_z = position['z'] + z_vector
        return {'x': target_x, 'y': position['y'], 'z': target_z}

    def calc_walked_into_structures(self):
        ''' 
        Determine the number of times that the performer walked into
        walls, platform walls, ramp sides, and occluders.
        Platform lips are exluded.
        '''
        steps_list = self.history['steps']
        walked_into_structures = 0
        structures = [obj for obj in self.scene['objects']
            if obj.get('structure') is True]
        bounding_boxes = [
            {'id': struct['id'], 'bounding_box': struct['shows'][0]['boundingBox']}
            for struct in structures]
        ramp_bounding_boxes = [
            {'id': struct['id'], 'bounding_box': struct['shows'][0]['boundingBox']}
            for struct in structures if struct['id'].startswith('ramp')]
        default_room_dimensions = {'x': 10, 'y': 3, 'z': 10}
        room_dimensions = self.scene.get('roomDimensions', default_room_dimensions)
        
        # Keeps track of obstruction ids, this is not being used now but may be useful
        obstructions = []
        
        move_actions = ['MoveAhead', 'MoveBack', 'MoveLeft', 'MoveRight']
        for single_step in steps_list:
            action = single_step['action']
            output = single_step['output']
            if action in move_actions and output['return_status'] == 'OBSTRUCTED':
                performers_target_point = (
                    self.get_performer_target_point_based_on_direction(
                        output['position'], output['rotation'], action))
                obstructed_by_wall, id = (self.point_is_outside_room_dimensions(
                    performers_target_point, room_dimensions))
                if obstructed_by_wall:
                    walked_into_structures += 1
                    obstructions.append(id)
                    continue
                for bb in bounding_boxes:
                    inside = self.point_is_inside_bounding_box(
                        performers_target_point, bb['bounding_box'])
                    """
                    Check if the obstruction is a platform lip
                    with the edge case of walking up a ramp 
                    and hitting the side or outside of the lip while still
                    on the ramp and not on top of the platform
                    """
                    if inside and bb['id'].startswith('platform'):
                        is_on_ramp = False
                        for bb_ramp_check in ramp_bounding_boxes:
                            if (self.point_is_inside_bounding_box(
                                output['position'], bb_ramp_check['bounding_box'])):
                                is_on_ramp = True
                                break
                        if is_on_ramp:
                            break
                    if inside:
                        obstructions.append(bb['id'])
                        walked_into_structures += 1
                        break
        self.walked_into_structures = walked_into_structures
        return self.walked_into_structures

    def calc_num_rewards_achieved(self):
        '''
        Determine the number of reward soccer balls collected by
        the performer.
        '''
        # Ignore passive scenes
        if(self.scene["goal"]["sceneInfo"]["primaryType"] != "interactive"):
            return None

        steps_list = self.history['steps']

        # track targets that are held
        targets_picked_up = []

        for single_step in steps_list:
            action = single_step['action']
            output = single_step['output']

            if action == 'PickupObject' and output['return_status'] == 'SUCCESSFUL':
                # Get the id of the object that was used, if any
                obj_id = get_relevant_object(output)

                if is_obj_target(self.scene, obj_id) and (obj_id not in targets_picked_up):
                    targets_picked_up.append(obj_id)

        self.number_of_rewards_achieved = len(targets_picked_up)
        logging.debug(f"Total number of rewards achieved: {self.number_of_rewards_achieved}")
        return self.number_of_rewards_achieved

    def calc_imitation_order_containers_are_opened_colors(self):
        ''' 
        Determine the order the performer opened containers by color
        '''
        steps_list = self.history['steps']
        order_containers_are_opened_colors = []

        containers = [(obj['id'], obj['debug']['color']) for obj in self.scene['objects']
            if obj['type'].startswith('chest')]
        for single_step in steps_list:
            action = single_step['action']
            output = single_step['output']
            if (action == 'OpenObject'):
                resolved_obj_id = output['resolved_object']
                if output['return_status'] == "SUCCESSFUL":
                    for c in containers:
                         if resolved_obj_id == c[0]:
                            order_containers_are_opened_colors.append(c[1])

        self.order_containers_are_opened_colors = \
            order_containers_are_opened_colors
        return self.order_containers_are_opened_colors

    def calc_set_rotation(self):
        ''' 
        Determine the container the performer opened in set rotation scenes
        '''
        steps_list = self.history['steps']
        """
        Absolute Container Position
             1
             |  
        4 -- 5 -- 2
             |  
             3
          Performer
        """
        absolute_positions = {
            1: (0, 2.62),
            2: (1.62, 1),
            3: (0, 0.62),
            4: (-1.62, 1),
            5: (0, 1)
        }
        self.set_rotation_opened_container_position_absolute = ''
        self.set_rotation_opened_container_position_relative_to_baited = ''
        if (not self.scene['goal']['sceneInfo'].get('tertiaryType') or
                self.scene['goal']['sceneInfo']['tertiaryType'] != "set rotation"):
            self.set_rotation_opened_container_position_absolute = None
            self.set_rotation_opened_container_position_relative_to_baited = None
            return (self.set_rotation_opened_container_position_absolute,
                    self.set_rotation_opened_container_position_relative_to_baited)
        try:
            containers_and_lids = [
                {
                    'id': obj['id'],
                    'lid': obj['debug']['lidId'],
                    'start_position_x': obj['shows'][0]['position']['x'],
                    'start_position_z': obj['shows'][0]['position']['z'],
                    'absolute_pos_start': None,
                    'absolute_pos_end': None,
                    'relative_to_baited': None
                }
                for obj in self.scene['objects'] if obj['type'] == 'separate_container']
            rotation_direction = self.scene['goal']['sceneInfo'].get('rotation')
            rotation = self.scene['goal']['sceneInfo'].get('degreesRotated')

            if rotation_direction is None or rotation is None:
                self.set_rotation_opened_container_position_absolute = None
                self.set_rotation_opened_container_position_relative_to_baited = None
                return (self.set_rotation_opened_container_position_absolute,
                        self.set_rotation_opened_container_position_relative_to_baited)

            # absolute
            for cl in containers_and_lids:
                absolute_pos = [
                    k for k, v in absolute_positions.items() if
                    cl['start_position_x'] == v[0] and cl['start_position_z'] == v[1]][0]
                cl['absolute_pos_start'] = absolute_pos
                if absolute_pos == 5:
                    cl['absolute_pos_end'] = absolute_pos
                    continue
                increments = int(rotation / 90 * (
                    -1 if rotation_direction.startswith('counter') else 1))
                edge_positions = [1, 2, 3, 4]
                end_pos = edge_positions[
                    (edge_positions.index(absolute_pos) + increments) % len(edge_positions)]
                cl['absolute_pos_end'] = end_pos

            # relative
            target_x = self.scene['objects'][0]['shows'][0]['position']['x']
            isSideContainer = target_x != 0
            if isSideContainer:
                for cl in containers_and_lids:
                    cl['relative_to_baited'] = (
                        'baited' if cl['start_position_x'] == target_x else
                        'middle' if cl['start_position_x'] == 0 else
                        'opposite')
            else:
                absolute_pos_to_relative_dict = {1: 'far', 2: 'right', 3: 'near', 4: 'left'}
                for cl in containers_and_lids:
                    if cl['start_position_x'] == target_x:
                        cl['relative_to_baited'] = 'baited'
                    else:
                        cl['relative_to_baited'] = \
                            absolute_pos_to_relative_dict[cl['absolute_pos_end']]

            found_container = False
            for single_step in steps_list:
                action = single_step['action']
                output = single_step['output']
                if (action == 'OpenObject'):
                    resolved_obj_id = output['resolved_object']
                    if output['return_status'] == "SUCCESSFUL":
                        for cl in containers_and_lids:
                            if resolved_obj_id == cl['id'] or resolved_obj_id == cl['lid']:
                                self.set_rotation_opened_container_position_absolute = \
                                    str(cl['absolute_pos_start']) + ' to ' + str(cl['absolute_pos_end'])
                                self.set_rotation_opened_container_position_relative_to_baited = \
                                    cl['relative_to_baited']
                                break
                if found_container:
                    break
            self.set_rotation_opened_container_position_absolute = \
                self.set_rotation_opened_container_position_absolute
            self.set_rotation_opened_container_position_relative_to_baited = \
                self.set_rotation_opened_container_position_relative_to_baited
        except:
            pass
        finally:
            return (self.set_rotation_opened_container_position_absolute,
                    self.set_rotation_opened_container_position_relative_to_baited)

    def calc_shell_game(self):
        ''' 
        Determine the container the performer opened in shell game scenes
        '''
        steps_list = self.history['steps']
        shell_game_opened_container = None
        baited_ctr_end_pos = None
        baited_ctr_id = None
        if (not self.scene['goal']['sceneInfo'].get('tertiaryType') or
                self.scene['goal']['sceneInfo']['tertiaryType'] != "shell game"):
            self.shell_game_opened_container_position_relative_to_baited = None
            self.shell_game_opened_container = shell_game_opened_container
            return self.shell_game_opened_container_position_relative_to_baited, self.shell_game_opened_container
        containers_and_lids = [
            {
                'id': obj['id'],
                'lid': obj['debug']['lidId'],
                'isTargetContainer': obj['debug'].get('isTargetContainer'),
                'position_x': obj['shows'][0]['position']['x'],
                'moves': obj.get('moves')
            }
            for obj in self.scene['objects'] if obj['type'] == 'separate_container']

        if('baitedContainerMovement' in self.scene['goal']['sceneInfo']):
            baited_ctr_end_pos = self.scene['goal']['sceneInfo']['baitedContainerMovement'][-1]
        else:
            # in case the tag isn't in the scene file, calculate baited container movement
            for cl in containers_and_lids:
                if cl['isTargetContainer']:
                    baited_ctr_end_pos = find_shell_game_container_start_end(cl)[-1]
                    baited_ctr_id = cl['id']
                    break

        relative_pos = None
        found_container = False
        for single_step in steps_list:
            action = single_step['action']
            output = single_step['output']
            if (action == 'OpenObject'):
                resolved_obj_id = output['resolved_object']
                if output['return_status'] == "SUCCESSFUL":
                    for cl in containers_and_lids:
                        if resolved_obj_id == cl['id'] or resolved_obj_id == cl['lid']:
                            shell_game_opened_container = find_shell_game_container_start_end(cl)
                            opened_ctr_end_pos = shell_game_opened_container[-1]

                            # if the opened container was the baited one, no additional calculations needed
                            if(opened_ctr_end_pos == baited_ctr_end_pos):
                                relative_pos = 'baited'
                            else:
                                # if a non-baited container was opened
                                if(self.scene['goal']['sceneInfo']['numberOfContainers'] == 2):
                                    relative_pos = ('left' if opened_ctr_end_pos < baited_ctr_end_pos else 'right')
                                else:
                                    # three container case
                                    # we have the opened container info and the baited one, figure out where the third one is to get
                                    # relative position of opened one to baited
                                    third_ctr = [cl for cl in containers_and_lids if (cl['id'] not in [resolved_obj_id, baited_ctr_id])][0]
                                    third_ctr_end_pos = find_shell_game_container_start_end(third_ctr)[-1]

                                    if ((baited_ctr_end_pos < third_ctr_end_pos and baited_ctr_end_pos > opened_ctr_end_pos) or
                                        (baited_ctr_end_pos < opened_ctr_end_pos and baited_ctr_end_pos > third_ctr_end_pos)):
                                        # baited is in the middle
                                        relative_pos = 'left' if opened_ctr_end_pos < baited_ctr_end_pos else 'right'
                                    else:
                                        # baited is on one of the ends
                                        if(baited_ctr_end_pos < third_ctr_end_pos and baited_ctr_end_pos < opened_ctr_end_pos):
                                            # baited on left
                                            relative_pos = 'middle' if opened_ctr_end_pos < third_ctr_end_pos else 'opposite'
                                        else:
                                            # baited on right
                                            relative_pos = 'middle' if third_ctr_end_pos < opened_ctr_end_pos else 'opposite'

                            found_container = True
                            break
            if found_container:
                break

        self.shell_game_opened_container_position_relative_to_baited = relative_pos
        self.shell_game_opened_container = shell_game_opened_container
        return self.shell_game_opened_container_position_relative_to_baited, self.shell_game_opened_container

    def calc_door_opened_side(self):
        ''' 
        Determine the door the performer opened in the following scenes
        with the options available:
        Trajectory - Left, Right
        InteractiveCollision - Left, Right
        Solidity - Left, Middle, Right
        SupportRelations - Left, Middle, Right
        '''
        steps_list = self.history['steps']
        door_opened = None

        doors = [
            [obj['id'], obj['shows'][0]['position']['x']]
            for obj in self.scene['objects'] if obj['type'].startswith('door')]
        found_door = False
        for single_step in steps_list:
            action = single_step['action']
            output = single_step['output']
            if (action == 'OpenObject'):
                resolved_obj_id = output['resolved_object']
                if output['return_status'] == "SUCCESSFUL":
                    for door in doors:
                        if resolved_obj_id == door[0]:
                            door_opened = \
                                'left' if door[1] < 0 else \
                                    'middle' if door[1] == 0 else 'right'
                            found_door = True
                            break
            if found_door:
                break

        self.door_opened_side = door_opened
        return self.door_opened_side

    def calc_interacted_with_blob_first(self):
        ''' 
        Determine if the performer went to the blob first in
        the following scenes: Holes, Lava, Ramps
        '''
        steps_list = self.history['steps']

        interacted_with_blob_first = False
        agent = [obj['id'] for obj in self.scene['objects'] if obj['type'].startswith('agent')]
        blob = [obj['id'] for obj in self.scene['objects'] if obj['type'].startswith('blob')]
        if len(agent) and len(blob):
            for single_step in steps_list:
                action = single_step['action']
                output = single_step['output']
                if (action == 'InteractWithAgent'):
                    resolved_obj_id = output['resolved_object']
                    if output['return_status'] == "NOT_AGENT":
                        if resolved_obj_id == blob[0]:
                            interacted_with_blob_first = True
                            break
                    if output['return_status'] == "SUCCESSFUL":
                        if resolved_obj_id == agent[0]:
                            interacted_with_blob_first = False
                            break

        self.interacted_with_blob_first = interacted_with_blob_first
        return self.interacted_with_blob_first

    def calc_stepped_in_lava(self):
        if('lava' not in self.scene):
            return None

        stepped_in_lava = False
        last_step = self.history['steps'][-1]
        output = last_step['output']
        if(output['steps_on_lava'] > 0):
            stepped_in_lava = True

        self.stepped_in_lava = stepped_in_lava
        return self.stepped_in_lava
