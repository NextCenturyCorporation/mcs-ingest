#
# Scorecard tests on individual functions, passing in locally generated
# data.
#
import logging
import unittest

import numpy as np

import mcs_scene_ingest
from scorecard import (
    Scorecard,
    calc_repeat_failed,
    find_closest_container,
    find_target_loc_by_step,
    get_lookpoint,
)
import scorecard

TEST_SCENE_FILE_NAME = "occluders_0001_17_I1_debug.json"
TEST_HISTORY_FILE_NAME = "india_0003_baseline_level1.json"

TEST_SCENE_CONTAINER = "golf_0018_15_debug.json"
TEST_HISTORY_CONTAINER = "golf_0018_15_baseline.json"

TEST_SCENE_MOVING_TARGET = "alpha_0001_03_debug.json"
TEST_HISTORY_MOVING_TARGET_PASS = "alpha_0001_03_test_pass.json"
TEST_HISTORY_MOVING_TARGET_FAIL = "alpha_0001_03_test_fail.json"

TEST_SCENE_NO_TARGET = "juliett_0001_01_debug.json"
TEST_HISTORY_NO_TARGET = "test_eval_3-5_level2_baseline_juliett_0001_01.json"

TEST_SCENE_RAMP = "ramps_eval_5_ex_1.json"
TEST_HISTORY_RAMP_UP_DOWN = "ramps_test_all_combos.json"

TEST_SCENE_SIDE = "prefix_0001_01_C4_debug.json"
TEST_HISTORY_SIDE_1 = "gen_platform_side_1.json"
TEST_HISTORY_SIDE_2 = "gen_platform_side_2.json"
TEST_HISTORY_SIDE_3 = "gen_platform_side_3.json"

TEST_SCENE_TOOL_CHOICE_SIDE = "lima_0001_06_debug.json"
TEST_HISTORY_TOOL_CHOICE_SIDE_CORRECT = (
    "lima_0001_06_correct_side_history.json"
)
TEST_HISTORY_TOOL_CHOICE_SIDE_INCORRECT = (
    "lima_0001_06_incorrect_side_history.json"
)

TEST_SCENE_DOOR_OPENED = "prefix_0001_02_I1_debug.json"
TEST_HISTORY_DOOR_CORRECT = "gen_correct_door_ex.json"
TEST_HISTORY_DOOR_INCORRECT = "gen_incorrect_door_ex.json"

TEST_SCENE_INTERACT_WITH_NON_AGENT = "non_agent_scene.json"
TEST_HISTORY_INTERACT_WITH_NON_AGENT = "non_agent_history.json"
TEST_SCENE_NOT_PICKUPABLE = "not_pickupable.json"
TEST_HISTORY_NOT_PICKUPABLE = "not_pickupable_scene_history.json"
TEST_SCENE_OBSTRUCTED = "obstructed_scene.json"
TEST_HISTORY_OBSTRUCTED = "obstructed_history.json"
TEST_HISTORY_OBSTRUCTED_PLAFTORM_LIPS = "obstructed_history_just_plaform_lips.json"

TEST_SCENE_NUM_REWARDS = "arth_0001_13_ex.json"
TEST_SCENE_NUM_REWARDS_AMB = "num_comp_0003_05_scene.json"
TEST_HISTORY_NUM_REWARDS_ALL = "arth_0001_13_hist_all_targets.json"
TEST_HISTORY_NUM_REWARDS_PARTIAL = "arth_0001_13_hist_partial_targets.json"
TEST_HISTORY_NUM_REWARDS_INCORRECT = "arth_0001_13_hist_incorrect_target.json"
TEST_HISTORY_NUM_REWARDS_AMB_L = "num_comp_0003_05_hist_left.json"
TEST_HISTORY_NUM_REWARDS_AMB_R = "num_comp_0003_05_hist_right.json"

TEST_SCENE_IMITATION = "imitation_eval_5_ex_1.json"
TEST_HISTORY_IMITATION = "imitation_eval_5_ex_1_history.json"

TEST_SCENE_SET_ROTATION_TURNTABLE_MOVES_270_MIDDLE_BAITED_MIDDLE_PICKED = "set_rotation/setrotation_0001_17_I1_debug.json"
TEST_HISTORY_SET_ROTATION_TURNTABLE_270_COUNTER_CLOCKWISE = "set_rotation/setrotation_0001_17_history.json"

TEST_SCENE_SET_ROTATION_PERFORMER_MOVES_270_COUNTER_CLOCKWISE_LEFT_BAITED_LEFT_PICKED = "set_rotation/setrotation_0001_18_I2_debug.json"
TEST_HISTORY_SET_ROTATION_PERFORMER_270_COUNTER_CLOCKWISE_LEFT_BAITED_LEFT_PICKED = "set_rotation/setrotation_0001_18_history.json"

TEST_SCENE_SET_ROTATION_3_TABLE_270_CC_MIDDLE_BAITED_NEAR_PICKED = "set_rotation/setrotation_0002_17_I1_debug.json"
TEST_HISTORY_SET_ROTATION_3_TABLE_270_CC_MIDDLE_BAITED_NEAR_PICKED = "set_rotation/setrotation_0002_17_history.json"

TEST_SCENE_SET_ROTATION_3_PERF_270_CC_LEFT_BAITED_MIDDLE_PICKED = "set_rotation/setrotation_0002_18_I2_debug.json"
TEST_HISTORY_SET_ROTATION_3_PERF_270_CC_LEFT_BAITED_MIDDLE_PICKED = "set_rotation/setrotation_0002_18_history.json"

TEST_SCENE_SET_ROTATION_3_TABLE_180_CL_RIGHT_BAITED_RIGHT_PICKED = "set_rotation/setrotation_0003_11_F1_debug.json"
TEST_HISTORY_SET_ROTATION_3_TABLE_180_CL_RIGHT_BAITED_RIGHT_PICKED = "set_rotation/setrotation_0003_11_history.json"

TEST_SCENE_SET_ROTATION_2_TABLE_360_CL_LEFT_BAITED_RIGHT_PICKED = "set_rotation/setrotation_0003_21_K1_debug.json"
TEST_HISTORY_SET_ROTATION_2_TABLE_360_CL_LEFT_BAITED_RIGHT_PICKED = "set_rotation/setrotation_0003_21_history.json"

TEST_SCENE_SET_ROTATION_1_TABLE_90_CL_LEFT_BAITED_FAR_PICKED = "set_rotation/setrotation_0003_01_A1_debug.json"
TEST_HISTORY_SET_ROTATION_1_TABLE_90_CL_LEFT_BAITED_FAR_PICKED = "set_rotation/setrotation_0003_01_history.json"

TEST_SCENE_SET_ROTATION_5_TEST_5_TABLE_MOVES_90_CCW = "set_rotation/set_rotation_0005_33_M1_debug.json"
TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_90_CCW_CORRECT = "set_rotation/set_rotation_0005_33-ball-middle-correct.json"
TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_90_CCW_FAR_PICKED = "set_rotation/set_rotation_0005_33-ball-middle-opened-far.json"
TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_90_CCW_FAR_MID_PICKED = "set_rotation/set_rotation_0005_33-ball-middle-opened-far-mid.json"
TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_90_CCW_NEAR_MID_PICKED = "set_rotation/set_rotation_0005_33-ball-middle-opened-near-mid.json"
TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_90_CCW_NEAR_PICKED = "set_rotation/set_rotation_0005_33-ball-middle-opened-near.json"

TEST_SCENE_SET_ROTATION_5_TEST_5_TABLE_MOVES_180_CCW = "set_rotation/set_rotation_0005_37_N1_debug.json"
TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_180_CCW_CORRECT = "set_rotation/set_rotation_0005_37-ball-middle-correct.json"
TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_180_CCW_LEFT_MID_PICKED = "set_rotation/set_rotation_0005_37-ball-middle-opened-left-mid.json"
TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_180_CCW_RIGHT_MID_PICKED = "set_rotation/set_rotation_0005_37-ball-middle-opened-right-mid.json"
TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_180_CCW_LEFT_PICKED = "set_rotation/set_rotation_0005_37-ball-middle-opened-left.json"
TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_180_CCW_RIGHT_PICKED = "set_rotation/set_rotation_0005_37-ball-middle-opened-right.json"

TEST_SCENE_SET_ROTATION_5_TEST_6_TABLE_MOVES_90_CCW = "set_rotation/set_rotation_0006_33_M1_debug.json"
TEST_HISTORY_SET_ROTATION_5_TEST_6_TABLE_MOVES_90_CCW_CORRECT = "set_rotation/set_rotation_0006_33-ball-right-correct.json"
TEST_HISTORY_SET_ROTATION_5_TEST_6_TABLE_MOVES_90_CCW_LEFT_PICKED = "set_rotation/set_rotation_0006_33-ball-right-opened-left.json"
TEST_HISTORY_SET_ROTATION_5_TEST_6_TABLE_MOVES_90_CCW_LEFT_MID_PICKED = "set_rotation/set_rotation_0006_33-ball-right-opened-left-mid.json"
TEST_HISTORY_SET_ROTATION_5_TEST_6_TABLE_MOVES_90_CCW_RIGHT_MID_PICKED = "set_rotation/set_rotation_0006_33-ball-right-opened-right-mid.json"
TEST_HISTORY_SET_ROTATION_5_TEST_6_TABLE_MOVES_90_CCW_MIDDLE_PICKED = "set_rotation/set_rotation_0006_33-ball-right-opened-middle.json"

TEST_SCENE_SET_ROTATION_5_TEST_8_TABLE_MOVES_90_CW = "set_rotation/set_rotation_0008_33_M1_debug.json"
TEST_HISTORY_SET_ROTATION_5_TEST_8_TABLE_MOVES_90_CW_CORRECT = "set_rotation/set_rotation_0008_33-ball-rightmid-correct.json"
TEST_HISTORY_SET_ROTATION_5_TEST_8_TABLE_MOVES_90_CW_LEFT_PICKED = "set_rotation/set_rotation_0008_33-ball-rightmid-opened-left.json"
TEST_HISTORY_SET_ROTATION_5_TEST_8_TABLE_MOVES_90_CW_LEFT_MID_PICKED = "set_rotation/set_rotation_0008_33-ball-rightmid-opened-left-mid.json"
TEST_HISTORY_SET_ROTATION_5_TEST_8_TABLE_MOVES_90_CW_RIGHT_PICKED = "set_rotation/set_rotation_0008_33-ball-rightmid-opened-right.json"
TEST_HISTORY_SET_ROTATION_5_TEST_8_TABLE_MOVES_90_CW_MIDDLE_PICKED = "set_rotation/set_rotation_0008_33-ball-rightmid-opened-middle.json"

TEST_SCENE_SET_ROTATION_5_TEST_9_TABLE_MOVES_90_CCW = "set_rotation/set_rotation_0009_33_M1_debug.json"
TEST_HISTORY_SET_ROTATION_5_TEST_9_TABLE_MOVES_90_CCW_CORRECT = "set_rotation/set_rotation_0009_33-ball-leftmid-correct.json"
TEST_HISTORY_SET_ROTATION_5_TEST_9_TABLE_MOVES_90_CCW_LEFT_PICKED = "set_rotation/set_rotation_0009_33-ball-leftmid-opened-left.json"
TEST_HISTORY_SET_ROTATION_5_TEST_9_TABLE_MOVES_90_CCW_RIGHT_MID_PICKED = "set_rotation/set_rotation_0009_33-ball-leftmid-opened-right-mid.json"
TEST_HISTORY_SET_ROTATION_5_TEST_9_TABLE_MOVES_90_CCW_RIGHT_PICKED = "set_rotation/set_rotation_0009_33-ball-leftmid-opened-right.json"
TEST_HISTORY_SET_ROTATION_5_TEST_9_TABLE_MOVES_90_CCW_MIDDLE_PICKED = "set_rotation/set_rotation_0009_33-ball-leftmid-opened-middle.json"

TEST_SCENE_SET_ROTATION_5_TEST_10_TABLE_MOVES_90_CCW = "set_rotation/set_rotation_0010_33_M1_debug.json"
TEST_HISTORY_SET_ROTATION_5_TEST_10_TABLE_MOVES_90_CCW_CORRECT = "set_rotation/set_rotation_0010_33-ball-left-correct.json"
TEST_HISTORY_SET_ROTATION_5_TEST_10_TABLE_MOVES_90_CCW_LEFT_MID_PICKED = "set_rotation/set_rotation_0010_33-ball-left-opened-left-mid.json"
TEST_HISTORY_SET_ROTATION_5_TEST_10_TABLE_MOVES_90_CCW_RIGHT_MID_PICKED = "set_rotation/set_rotation_0010_33-ball-left-opened-right-mid.json"
TEST_HISTORY_SET_ROTATION_5_TEST_10_TABLE_MOVES_90_CCW_RIGHT_PICKED = "set_rotation/set_rotation_0010_33-ball-left-opened-right.json"
TEST_HISTORY_SET_ROTATION_5_TEST_10_TABLE_MOVES_90_CCW_MIDDLE_PICKED = "set_rotation/set_rotation_0010_33-ball-left-opened-middle.json"

TEST_SCENE_SHELL_GAME_CROSS_BAITED_PICKED_DISPLACEMENT = "shell_game/shellgame_0001_10_J1_debug.json"
TEST_HISTORY_SHELL_GAME_CROSS_BAITED_PICKED_DISPLACEMENT = "shell_game/shellgame_0001_10_history.json"

TEST_SCENE_SHELL_GAME_3_LATERAL_SUBSTITUTION_BAITED_PICKED_DISPLACEMENT = "shell_game/shellgame_0001_06_F1_debug.json"
TEST_HISTORY_SHELL_GAME_3_LATERAL_SUBSTITUTION_BAITED_PICKED_DISPLACEMENT = "shell_game/shellgame_0001_06_history.json"

TEST_SCENE_SHELL_GAME_2_LATERAL_BAITED_PICKED_NO_DISPLACEMENT = "shell_game/shellgame_0001_03_C1_debug.json"
TEST_HISTORY_SHELL_GAME_2_LATERAL_BAITED_PICKED_NO_DISPLACEMENT = "shell_game/shellgame_0001_03_history.json"

TEST_SCENE_SHELL_GAME_2_CROSS_CROSSED_PICKED_DISPLACEMENT = "shell_game/shellgame_0001_09_I1_debug.json"
TEST_HISTORY_SHELL_GAME_2_CROSS_CROSSED_PICKED_DISPLACEMENT = "shell_game/shellgame_0001_09_history.json"

TEST_SCENE_SHELL_GAME_3_LATERAL_SUBSTITUTION_SUBSTITUTED_PICKED_NO_DISPLACEMENT = "shell_game/shellgame_0001_08_H1_debug.json"
TEST_HISTORY_SHELL_GAME_3_LATERAL_SUBSTITUTION_SUBSTITUTED_PICKED_NO_DISPLACEMENT = "shell_game/shellgame_0001_08_history.json"

TEST_SCENE_UPDATED_SHELL_GAME_3_LATERAL_DISPLACEMENT = "shell_game/shell-game_0004_02_B1_debug.json"
TEST_HISTORY_UPDATED_SHELL_GAME_3_LATERAL_DISPLACEMENT = "shell_game/shell-game_0004_02-left.json"

TEST_SCENE_UPDATED_SHELL_GAME_3_CROSS_DISPLACEMENT = "shell_game/shell-game_0004_10_J1_debug.json"
TEST_HISTORY_UPDATED_SHELL_GAME_3_CROSS_DISPLACEMENT_CORRECT = "shell_game/shell-game_0004_10-correct.json"
TEST_HISTORY_UPDATED_SHELL_GAME_3_CROSS_DISPLACEMENT_LEFT = "shell_game/shell-game_0004_10-left.json"

TEST_SCENE_INTERACTIVE_COLLISION_DOOR_OPENED = "door_side/interactive_collision_0001_03_C1_debug.json"
TEST_HISTORY_INTERACTIVE_COLLISION_DOOR_OPENED = "door_side/interactive_collision_0001_03_history.json"

TEST_SCENE_TRAJECTORY_DOOR_OPENED = "door_side/trajectory_0001_03_C1_debug.json"
TEST_HISTORY_TRAJECTORY_DOOR_OPENED = "door_side/trajectory_0001_03_history.json"

TEST_SCENE_SOLIDITY_DOOR_OPENED = "door_side/solidity_0001_03_C1_debug.json"
TEST_HISTORY_SOLIDITY_DOOR_OPENED = "door_side/solidity_0001_03_history.json"

TEST_SCENE_SUPPORT_RELATIONS_DOOR_OPENED = "door_side/support_relations_0001_09_I1_debug.json"
TEST_HISTORY_SUPPORT_RELATIONS_DOOR_OPENED = "door_side/support_relations_0001_history.json"

TEST_SCENE_INTERACTED_WITH_BLOB_FIRST_HOLES = "interact_with_blob_first/holes_0001_08_D2_debug.json"
TEST_HISTORY_INTERACTED_WITH_BLOB_FIRST_HOLES = "interact_with_blob_first/holes_0001_history.json"

TEST_SCENE_INTERACTED_WITH_BLOB_FIRST_LAVA = "interact_with_blob_first/lava_0001_08_D2_debug.json"
TEST_HISTORY_INTERACTED_WITH_BLOB_FIRST_LAVA = "interact_with_blob_first/lava_0001_history.json"

TEST_SCENE_INTERACTED_WITH_BLOB_FIRST_RAMPS = "interact_with_blob_first/ramps_0001_23_P2_debug.json"
TEST_HISTORY_INTERACTED_WITH_BLOB_FIRST_RAMPS = "interact_with_blob_first/ramps_0001_history.json"

TEST_SCENE_TOOL_CHOICE = "tool_choice_scene_debug.json"
TEST_HISTORY_TOOL_CHOICE_PICKUP_FAILED = (
    "tool_choice_pickup_failed_history.json"
)
TEST_HISTORY_TOOL_CHOICE_PICKUP_NON_TARGET = (
    "tool_choice_pickup_non_target_history.json"
)
TEST_HISTORY_TOOL_CHOICE_PICKUP_NOTHING = (
    "tool_choice_pickup_nothing_history.json"
)
TEST_HISTORY_TOOL_CHOICE_PICKUP_TARGET = (
    "tool_choice_pickup_target_history.json"
)

TEST_SCENE_TOOL_USE = "eval_6_lima_0001_02_debug.json"
TEST_HISTORY_TOOL_USE = "eval_6_lima_0001_02_tool_usage_hist.json"

TEST_SCENE_MULTI_TOOL = "multi_tool/multi-tool_0001_01_scene_debug.json"
TEST_HISTORY_MULTI_TOOL_BOTH_TOOLS_ROTATED = "multi_tool/multi-tool_0001_01_both_rotated.json"
TEST_HISTORY_MULTI_TOOL_NO_TOOLS_USED = "multi_tool/multi-tool_0001_01_no_tools_used.json"
TEST_HISTORY_MULTI_TOOL_HOOKED_ROTATED = "multi_tool/multi-tool_0001_01_hooked_tool_rotated.json"
TEST_HISTORY_MULTI_TOOL_RECT_ROTATED = "multi_tool/multi-tool_0001_01_rect_tool_rotated.json"

TEST_SCENE_LAVA_STEP = "eval_6_mars_0010_01_debug.json"
TEST_HISTORY_LAVA_STEP = "eval_6_mars_0010_01_lava_step_hist.json"

TEST_FOLDER = "./tests/test_data"

# Hide all non-error log messages while running these unit tests.
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def create_mock_step(
        action: str = 'Pass',
        object_coords: dict = None,
        object_id: str = None,
        receptacle_object_id: str = None,
        position: dict = None,
        resolved_object=None,
        resolved_receptacle=None,
        receptacle_coords: dict = None,
        return_status: str = 'SUCCESSFUL',
        rotation: int = 0
) -> dict:
    return {
        'action': action,
        'output': {
            'position': position or {'x': 0, 'y': 0, 'z': 0},
            'return_status': return_status,
            'rotation': rotation,
            'resolved_object': resolved_object,
            'resolved_receptacle': resolved_receptacle
        },
        'params': {
            'objectImageCoords': object_coords or {'x': 0, 'y': 0},
            'receptacleObjectImageCoords': (
                receptacle_coords or {'x': 0, 'y': 0},
            ),
            'objectId': object_id,
            'receptacleObjectId': object_id
        }
    }


class TestMcsScorecard(unittest.TestCase):
    gt_tests = None

    def test_get_grid_by_location(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_FILE_NAME)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_FILE_NAME)
        scorecard = Scorecard(history_file, scene_file)

        x1 = -2.006410598754883
        z1 = 0.6039760112762451
        gx1, gz1 = scorecard.get_grid_by_location(x1, z1)

        x2 = -2.4064102172851562
        z2 = 0.6039760112762451
        gx2, gz2 = scorecard.get_grid_by_location(x2, z2)
        self.assertEqual(gx1, gx2, 'Grid values are different ' +
                         f'for {x1} {x2}: {gx1} {gx2}')
        self.assertEqual(gz1, gz2, 'Grid values are different ' +
                         f'for {z1} {z2}: {gz1} {gz2}')

    def test_find_closest_container(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_CONTAINER)

        # Make sure it finds chest_3 at chest_3 location
        x = -3.04
        z = 0.66
        container = find_closest_container(x, z, scene_file)
        self.assertEqual(container['type'], 'chest_3')
        logging.info(f"Closest:  {container}")

        # Give location between chest_3 and case_3, slightly closer to case_3
        x = -3.13
        z = 2.25
        container = find_closest_container(x, z, scene_file)
        self.assertEqual(container['type'], 'case_3')
        logging.info(f"Closest:  {container}")

    def test_find_closest_container_but_none(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_FILE_NAME)

        x = -3.04
        z = 0.66
        container = find_closest_container(x, z, scene_file)
        self.assertEqual(container, [])

    def test_load_json_file(self):
        # Will log a "step data" warning due to using an old scene history file
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_FILE_NAME)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_FILE_NAME)
        scorecard = Scorecard(history_file, scene_file)
        scorecard_vals = scorecard.score_all()
        repeats = scorecard_vals["repeat_failed"]['total_repeat_failed']
        self.assertEqual(repeats, 0)
        self.assertEqual(scorecard_vals["revisits"], 1)
        logging.debug(f"{scorecard_vals}")

    def test_score_all_keys(self):
        # Will log a "step data" warning due to using an old scene history file
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_FILE_NAME)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_FILE_NAME)
        scorecard = Scorecard(history_file, scene_file)
        scorecard_vals = scorecard.score_all()
        self.assertEqual(list(scorecard_vals.keys()), [
            'repeat_failed',
            'attempt_impossible',
            'correct_door_opened',
            'correct_platform_side',
            'open_unopenable',
            'container_relook',
            'not_moving_toward_object',
            'revisits',
            'fastest_path',
            'ramp_actions',
            'tool_usage',
            'pickup_non_target',
            'pickup_not_pickupable',
            'interact_with_non_agent',
            'walked_into_structures',
            'interact_with_agent' ,
            'number_of_rewards_achieved',
            'order_containers_are_opened_colors',
            'set_rotation_opened_container_position_absolute',
            'set_rotation_opened_container_position_relative_to_baited',
            'shell_game_opened_container_position_relative_to_baited',
            'shell_game_opened_container',
            'door_opened_side',
            'interacted_with_blob_first',
            'stepped_in_lava']
        )

    def test_get_lookpoint(self):
        # THOMAS Not computing dist, tilt is 0.0
        import numpy as np
        import math

        # Not looking down, so no lookpoint
        # Will log a warning due to the tilt being 0
        x, z = get_lookpoint(0., 0., 0., 0., 0.)
        np.testing.assert_almost_equal(x, 0.)
        np.testing.assert_almost_equal(z, 0.)

        # Looking down 45 along Z, so distance equal to height
        x, z = get_lookpoint(0., 1., 0., 0., 45.)
        np.testing.assert_almost_equal(x, 0.)
        np.testing.assert_almost_equal(z, 1.)

        # Looking back to right, down 30 so dist is sqrt(2)/2, w/ z neg
        x, z = get_lookpoint(0., 1., 0., 135., 45.)
        sqrt2over2 = math.sqrt(2) / 2.
        np.testing.assert_almost_equal(x, sqrt2over2)
        np.testing.assert_almost_equal(z, -sqrt2over2)

        # In back left corner, looking slightly left
        x, z = get_lookpoint(-3., 1., -3., -10., 18.)
        np.testing.assert_almost_equal(x, -3.5344, decimal=4)
        np.testing.assert_almost_equal(z, 0.03093, decimal=4)

        # Same as previous but angle is different representation.
        x, z = get_lookpoint(-3., 1., -3., 350., 18.)
        np.testing.assert_almost_equal(x, -3.5344, decimal=4)
        np.testing.assert_almost_equal(z, 0.03093, decimal=4)

    def test_find_target_location_no_target(self):
        '''Test trying to find a target, when there is not one'''
        # Will log a "step data" warning due to using an old scene history file
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_NO_TARGET)
        hist_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_NO_TARGET)
        target_id, x, z = find_target_loc_by_step(scene_file,
                                                  hist_file["steps"][0])
        self.assertFalse(target_id, "Target should not exist, " +
                         f"but it does {x} {z}")

    def test_find_target_location_with_target(self):
        '''Test trying to find a target, when there is not one'''
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_MOVING_TARGET)
        hist_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_MOVING_TARGET_PASS)
        target_id, x, z = find_target_loc_by_step(scene_file,
                                                  hist_file["steps"][0])
        if target_id is None:
            self.fail("Target not found")
        np.testing.assert_almost_equal(x, -3.654195547103882,
                                       err_msg="x location is wrong")
        np.testing.assert_almost_equal(z, 3.75,
                                       err_msg="Z location is wrong")

    def test_calc_not_moving_toward_object_zero(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_MOVING_TARGET)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_MOVING_TARGET_PASS)
        scorecard = Scorecard(history_file, scene_file)
        not_moving = scorecard.calc_not_moving_toward_object()
        self.assertEqual(not_moving, 0)

    def test_calc_not_moving_toward_object_greater_than_zero(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_MOVING_TARGET)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_MOVING_TARGET_FAIL)
        scorecard = Scorecard(history_file, scene_file)
        not_moving = scorecard.calc_not_moving_toward_object()
        self.assertGreater(not_moving, 0)

    def test_calc_repeat_failed_ignore_failed(self):
        # Will log some warnings due to failed actions
        repeat_failed = calc_repeat_failed([
            create_mock_step(action='MoveAhead', return_status='FAILED'),
            create_mock_step(action='MoveAhead', return_status='FAILED')
        ])
        self.assertEqual(repeat_failed['total_repeat_failed'], 0)

    def test_calc_repeat_failed_ignore_obstructed(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(action='MoveAhead', return_status='OBSTRUCTED'),
            create_mock_step(action='MoveAhead', return_status='OBSTRUCTED')
        ])
        self.assertEqual(repeat_failed['total_repeat_failed'], 0)

    def test_calc_repeat_failed_one_success(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200}
            )
        ])
        self.assertEqual(repeat_failed['total_repeat_failed'], 0)

    def test_calc_repeat_failed_one_failure(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                return_status='OUT_OF_REACH'
            )
        ])
        self.assertEqual(repeat_failed['total_repeat_failed'], 0)

    def test_calc_repeat_failed_two_failures(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                return_status='OUT_OF_REACH'
            ),
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                return_status='OUT_OF_REACH'
            )
        ])
        self.assertEqual(repeat_failed['total_repeat_failed'], 1)

    def test_calc_repeat_failed_three_failures(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                return_status='OUT_OF_REACH'
            ),
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                return_status='OUT_OF_REACH'
            ),
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                return_status='OUT_OF_REACH'
            )
        ])
        self.assertEqual(repeat_failed['total_repeat_failed'], 2)

    def test_calc_repeat_failed_two_failures_with_pause_in_between(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                return_status='OUT_OF_REACH'
            ),
            create_mock_step(),
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                return_status='OUT_OF_REACH'
            )
        ])
        self.assertEqual(repeat_failed['total_repeat_failed'], 1)

    def test_calc_repeat_failed_two_failures_different_action(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='CloseObject',
                object_coords={'x': 300, 'y': 200},
                return_status='OUT_OF_REACH'
            ),
            create_mock_step(
                action='OpenObject',
                object_coords={'x': 300, 'y': 200},
                return_status='OUT_OF_REACH'
            )
        ])
        self.assertEqual(repeat_failed['total_repeat_failed'], 0)

    def test_calc_repeat_failed_two_failures_different_params(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='PickupObject',
                resolved_object='wall_back',
                return_status='OUT_OF_REACH'
            ),
            create_mock_step(
                action='PickupObject',
                resolved_object='wall_left',
                return_status='OUT_OF_REACH'
            )
        ])
        self.assertEqual(repeat_failed['total_repeat_failed'], 0)

    def test_calc_repeat_failed_two_failures_different_position(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                position={'x': 0, 'y': 0, 'z': 0},
                return_status='OUT_OF_REACH'
            ),
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                position={'x': 1, 'y': 0, 'z': 0},
                return_status='OUT_OF_REACH'
            )
        ])
        self.assertEqual(repeat_failed['total_repeat_failed'], 0)

    def test_calc_repeat_failed_two_failures_different_rotation(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                return_status='OUT_OF_REACH',
                rotation=0
            ),
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                return_status='OUT_OF_REACH',
                rotation=10
            )
        ])
        self.assertEqual(repeat_failed['total_repeat_failed'], 0)

    def test_calc_repeat_failed_two_failures_different_status(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                return_status='OUT_OF_REACH'
            ),
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                return_status='NOT_OBJECT'
            )
        ])
        self.assertEqual(repeat_failed['total_repeat_failed'], 0)

    def test_calc_repeat_failed_object_id_not_visible_status(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='PickupObject',
                object_id='ball',
                return_status='NOT_VISIBLE'
            ),
            create_mock_step(
                action='PickupObject',
                object_id='ball',
                return_status='NOT_VISIBLE'
            ),
            create_mock_step(),
            create_mock_step(
                action='PickupObject',
                object_id='ball',
                return_status='NOT_VISIBLE'
            ),
        ])
        self.assertEqual(repeat_failed['total_repeat_failed'], 2)

    def test_calc_repeat_failed_receptacle_object_id_not_visible_status(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='PickupObject',
                receptacle_object_id='container',
                return_status='NOT_VISIBLE'
            ),
            create_mock_step(
                action='PickupObject',
                receptacle_object_id='container',
                return_status='NOT_VISIBLE'
            ),
            create_mock_step(),
            create_mock_step(
                action='PickupObject',
                receptacle_object_id='container',
                return_status='NOT_VISIBLE'
            ),
        ])
        self.assertEqual(repeat_failed['total_repeat_failed'], 2)


    def test_calc_repeat_failed_receptacle_object_id_and_object_id_not_visible_status(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='PickupObject',
                receptacle_object_id='container',
                return_status='NOT_VISIBLE'
            ),
            create_mock_step(
                action='PickupObject',
                object_id='container',
                return_status='NOT_VISIBLE'
            ),
            create_mock_step(),
            create_mock_step(
                action='PickupObject',
                receptacle_object_id='container',
                return_status='NOT_VISIBLE'
            ),
            create_mock_step(
                action='PickupObject',
                object_id='container',
                return_status='NOT_VISIBLE'
            ),
        ])
        self.assertEqual(repeat_failed['total_repeat_failed'], 3)

    def test_on_ramp(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_RAMP)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_RAMP_UP_DOWN)
        scorecard = Scorecard(history_file, scene_file)

        # Lower ramp pos (1.5, 1), size (2,1)
        position = {'x': 1.51, 'z': 1.1}
        on_ramp_bool, rot, ramp_id = scorecard.on_ramp(position)
        self.assertTrue(on_ramp_bool)
        self.assertEqual(ramp_id, "ramp_lower")

        position = {'x': 3.51, 'z': 1.1}
        on_ramp_bool, rot, ramp_id = scorecard.on_ramp(position)
        self.assertFalse(on_ramp_bool)
        self.assertEqual(ramp_id, "")

    def test_platform_side(self):
        # Robot leaves platform on correct side
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SIDE)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SIDE_1)
        scorecard = Scorecard(history_file, scene_file)

        correct_side = scorecard.calc_correct_platform_side()
        self.assertTrue(correct_side)

        # Robot leaves platform on incorrect side
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SIDE)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SIDE_2)
        scorecard = Scorecard(history_file, scene_file)

        correct_side = scorecard.calc_correct_platform_side()
        self.assertFalse(correct_side)

        # Robot stays on platform (incorrect)
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SIDE)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SIDE_3)
        scorecard = Scorecard(history_file, scene_file)

        correct_side = scorecard.calc_correct_platform_side()
        self.assertFalse(correct_side)

    def test_platform_side_triple_door(self):
        # Robot stays on platform (correct)
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_DOOR_OPENED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_DOOR_CORRECT)
        scorecard = Scorecard(history_file, scene_file)

        correct_side = scorecard.calc_correct_platform_side()
        self.assertTrue(correct_side)

        # Robot leaves platform on any side (incorrect)
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_DOOR_OPENED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_DOOR_INCORRECT)
        scorecard = Scorecard(history_file, scene_file)

        correct_side = scorecard.calc_correct_platform_side()
        self.assertFalse(correct_side)

    def test_platform_side_tool_choice(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_TOOL_CHOICE_SIDE)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_TOOL_CHOICE_SIDE_CORRECT)
        scorecard = Scorecard(history_file, scene_file)

        correct_side = scorecard.calc_correct_platform_side()
        self.assertTrue(correct_side)

        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_TOOL_CHOICE_SIDE)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_TOOL_CHOICE_SIDE_INCORRECT)
        scorecard = Scorecard(history_file, scene_file)

        correct_side = scorecard.calc_correct_platform_side()
        self.assertFalse(correct_side)

    def test_which_door(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_DOOR_OPENED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_DOOR_CORRECT)
        scorecard = Scorecard(history_file, scene_file)

        correct_door = scorecard.calc_correct_door_opened()
        self.assertTrue(correct_door)

        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_DOOR_OPENED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_DOOR_INCORRECT)
        scorecard = Scorecard(history_file, scene_file)

        correct_door = scorecard.calc_correct_door_opened()
        self.assertFalse(correct_door)

    def test_calc_fastest_path(self):
        history = {'steps':[
             {'output':{'position': {'x':-4, 'z':-4}}},
             {'output':{'position': {'x':-3.2, 'z':-3}}},
             {'output':{'position': {'x':-2.2, 'z':-2}}},
             {'output':{'position': {'x':-1.2, 'z':-1}}},
             {'output':{'position': {'x':-0.2, 'z':0}}},
             {'output':{'position': {'x':1, 'z':1}}}
        ]}
        
        history_slow = {'steps':[
             {'output':{'position': {'x':-4, 'z':-4}}},
             {'output':{'position': {'x':-4, 'z':-3.5}}},
             {'output':{'position': {'x':-4, 'z':-2.5}}},
             {'output':{'position': {'x':-4, 'z':-1.5}}},
             {'output':{'position': {'x':-4, 'z':-0.5}}},
             {'output':{'position': {'x':-4, 'z':0.5}}},
             {'output':{'position': {'x':-3.5, 'z':1}}},
             {'output':{'position': {'x':-2.5, 'z':1}}},
             {'output':{'position': {'x':-1.5, 'z':1}}},
             {'output':{'position': {'x':-0.5, 'z':1}}},
             {'output':{'position': {'x':0.5, 'z':1}}},
             {'output':{'position': {'x':1, 'z':1}}}
        ]}
        scene = {
             'performerStart': {'position':{'x':-4, 'z':-4}},
             'slowPath': [{'x':-4,'z':-4},
                    {'x':-4,'z':-3},
                    {'x':-4,'z':-2},
                    {'x':-4,'z':-1},
                    {'x':-4,'z':0},
                    {'x':-4,'z':1},
                    {'x':-3,'z':1},
                    {'x':-2,'z':1},
                    {'x':-1,'z':1},
                    {'x':0,'z':1}],
             'path': [{'x':2, 'z':2},
                        {'x':-3,'z':-3},
                        {'x':-2,'z':-2},
                        {'x':-1,'z':-1},
                        {'x':0,'z':0},
                        {'x':1,'z':1}
                        ]

        }
        sc=Scorecard(history, scene)
        sc.calc_fastest_path()
        assert sc.is_fastest_path
        
        sc=Scorecard(history_slow, scene)
        sc.calc_fastest_path()
        assert not sc.is_fastest_path
        
        scene.pop('slowPath')
        sc=Scorecard(history_slow, scene)
        sc.calc_fastest_path()
        assert sc.is_fastest_path is None
    
    def test_calc_interact_with_non_agent(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_INTERACT_WITH_NON_AGENT)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_INTERACT_WITH_NON_AGENT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_agent_interactions()
        assert scorecard.get_interact_with_non_agent() == 20
        assert scorecard.get_interact_with_agent() == 2

    def test_calc_pickup_not_pickupable(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_NOT_PICKUPABLE)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_NOT_PICKUPABLE)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_pickup_not_pickupable()
        assert scorecard.get_pickup_not_pickupable() == 19

    def test_number_of_times_walked_into_walls(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_OBSTRUCTED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_OBSTRUCTED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_walked_into_structures()
        assert scorecard.get_walked_into_structures() == 29

    def test_number_of_times_walked_into_platform_lips(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_OBSTRUCTED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_OBSTRUCTED_PLAFTORM_LIPS)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_walked_into_structures()
        # should be zero because this structure is not tracked
        assert scorecard.get_walked_into_structures() == 0

    def test_number_of_rewards_achieved_all(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_NUM_REWARDS)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_NUM_REWARDS_ALL)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_num_rewards_achieved()
        # should be 3, which is the total rewards for this scene
        assert scorecard.get_number_of_rewards_achieved() == 3

    def test_number_of_rewards_achieved_partial(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_NUM_REWARDS)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_NUM_REWARDS_PARTIAL)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_num_rewards_achieved()
        # should be 1, which isn't the total possible here
        assert scorecard.get_number_of_rewards_achieved() == 1

    def test_number_of_rewards_achieved_wrong(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_NUM_REWARDS)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_NUM_REWARDS_INCORRECT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_num_rewards_achieved()
        # should be 1, since the ball retrieved was a foil
        assert scorecard.get_number_of_rewards_achieved() == 0

    def test_number_of_rewards_achieved_retrieval(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_CONTAINER)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_CONTAINER)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_num_rewards_achieved()
        # should be 0 since reward ball wasn't achieved
        assert scorecard.get_number_of_rewards_achieved() == 0


    def test_number_of_rewards_achieved_non_interactive(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_NO_TARGET)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_NO_TARGET)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_num_rewards_achieved()
        # not applicable, should be None
        assert scorecard.get_number_of_rewards_achieved() == None

    def test_number_of_rewards_achieved_ambiguous_left(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_NUM_REWARDS_AMB)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_NUM_REWARDS_AMB_L)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_num_rewards_achieved()
        # should be 1 regardless of which side was chosen,
        # since a ball was picked up + scene is ambiguous
        assert scorecard.get_number_of_rewards_achieved() == 1

    def test_number_of_rewards_achieved_ambiguous_right(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_NUM_REWARDS_AMB)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_NUM_REWARDS_AMB_R)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_num_rewards_achieved()
        # should be 1 regardless of which side was chosen,
        # since a ball was picked up + scene is ambiguous
        assert scorecard.get_number_of_rewards_achieved() == 1

    def test_calc_imitation_order_containers_are_opened(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_IMITATION)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_IMITATION)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_imitation_order_containers_are_opened_colors()
        assert scorecard.get_imitation_order_containers_are_opened() == \
            [['orange'], ['blue']]

    def test_calc_set_rotation(self):
        # 3 containers, turntable moves 270 degrees counterclockwise, middle container is baited and picked
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SET_ROTATION_TURNTABLE_MOVES_270_MIDDLE_BAITED_MIDDLE_PICKED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_TURNTABLE_270_COUNTER_CLOCKWISE)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '5 to 5'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited'

        # 3 containers, turntable moves 270 degrees counterclockwise, left container is baited and picked
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SET_ROTATION_PERFORMER_MOVES_270_COUNTER_CLOCKWISE_LEFT_BAITED_LEFT_PICKED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_PERFORMER_270_COUNTER_CLOCKWISE_LEFT_BAITED_LEFT_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '4 to 1'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited'

        # 3 containers, turntable moves 270 degrees counterclockwise, middle container is baited,
        # near container is picked after the rotation
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SET_ROTATION_3_TABLE_270_CC_MIDDLE_BAITED_NEAR_PICKED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_3_TABLE_270_CC_MIDDLE_BAITED_NEAR_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '2 to 3'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'near'

        # 3 containers, performer moves 270 degrees counterclockwise, left container is baited,
        # middle container is picked after the rotation
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SET_ROTATION_3_PERF_270_CC_LEFT_BAITED_MIDDLE_PICKED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_3_PERF_270_CC_LEFT_BAITED_MIDDLE_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '5 to 5'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'middle'

        # 3 containers, turntable moves 180 degrees clockwise, right container is baited,
        # right container is picked after the rotation
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SET_ROTATION_3_TABLE_180_CL_RIGHT_BAITED_RIGHT_PICKED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_3_TABLE_180_CL_RIGHT_BAITED_RIGHT_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '4 to 2'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'opposite'

        # 2 containers, turntable moves 360 degrees clockwise, left container is baited,
        # right container is picked after the rotation
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SET_ROTATION_2_TABLE_360_CL_LEFT_BAITED_RIGHT_PICKED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_2_TABLE_360_CL_LEFT_BAITED_RIGHT_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '2 to 2'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'opposite'

        # 1 container, turntable moves 90 degrees clockwise, left container is baited,
        # far container is picked after the rotation
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SET_ROTATION_1_TABLE_90_CL_LEFT_BAITED_FAR_PICKED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_1_TABLE_90_CL_LEFT_BAITED_FAR_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '4 to 1'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited'


    def test_calc_set_rotation_five_container_baited_middle(self):
        # 5 containers, turntable moves 90 degrees counterclockwise, middle container is baited
        # history when middle container is picked
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SET_ROTATION_5_TEST_5_TABLE_MOVES_90_CCW)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_90_CCW_CORRECT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '5 to 5'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited'

        # history when furthest container picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_90_CCW_FAR_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '2 to 1'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'far'

        # history when container betweeen middle and furthest is picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_90_CCW_FAR_MID_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '7 to 6'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'farMiddle'

        # history when container betweeen middle and nearest is picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_90_CCW_NEAR_MID_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '9 to 8'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'nearMiddle'

        # history when nearest container is picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_90_CCW_NEAR_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '4 to 3'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'near'

        # 5 containers, turntable moves 180 degrees counterclockwise, middle container is baited
        # history when middle container is picked
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SET_ROTATION_5_TEST_5_TABLE_MOVES_180_CCW)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_180_CCW_CORRECT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '5 to 5'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited'

        # history when right-most container picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_180_CCW_RIGHT_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '4 to 2'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'right'

        # history when container betweeen middle and right is picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_180_CCW_RIGHT_MID_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '9 to 7'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'rightMiddle'

        # history when container betweeen middle and left is picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_180_CCW_LEFT_MID_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '7 to 9'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'leftMiddle'

        # history when right-most container picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_5_TABLE_MOVES_180_CCW_LEFT_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '2 to 4'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'left'


    def test_calc_set_rotation_five_container_baited_starts_on_right(self):
        # 5 containers, turntable moves 90 degrees counterclockwise, container starting on right is baited
        # history when right container is picked
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SET_ROTATION_5_TEST_6_TABLE_MOVES_90_CCW)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_6_TABLE_MOVES_90_CCW_CORRECT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '2 to 1'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited'

        # history when left container picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_6_TABLE_MOVES_90_CCW_LEFT_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '4 to 3'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'opposite'

        # history when container betweeen middle and right is picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_6_TABLE_MOVES_90_CCW_RIGHT_MID_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '7 to 6'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited - 1'

        # history when container betweeen middle and left is picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_6_TABLE_MOVES_90_CCW_LEFT_MID_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '9 to 8'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited - 3'

        # history when middle container is picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_6_TABLE_MOVES_90_CCW_MIDDLE_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '5 to 5'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited - 2'


    def test_calc_set_rotation_five_container_baited_starts_on_middle_right_flipped_labels(self):
        # 5 containers, turntable moves 90 degrees clockwise, container starting on middle right is baited
        # history when middle right container is picked
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SET_ROTATION_5_TEST_8_TABLE_MOVES_90_CW)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_8_TABLE_MOVES_90_CW_CORRECT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '7 to 8'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited'

        # history when left container picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_8_TABLE_MOVES_90_CW_LEFT_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '4 to 1'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited + 3'

        # history when container betweeen middle and left is picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_8_TABLE_MOVES_90_CW_LEFT_MID_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '9 to 6'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'opposite'

        # history when right container picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_8_TABLE_MOVES_90_CW_RIGHT_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '2 to 3'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited - 1'

        # history when middle container is picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_8_TABLE_MOVES_90_CW_MIDDLE_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '5 to 5'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited + 1'


    def test_calc_set_rotation_five_container_baited_starts_on_middle_left(self):
        # 5 containers, turntable moves 90 degrees counterclockwise, container starting on 
        # middle left is baited
        # history when middle left container is picked
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SET_ROTATION_5_TEST_9_TABLE_MOVES_90_CCW)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_9_TABLE_MOVES_90_CCW_CORRECT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '9 to 8'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited'

        # history when left container picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_9_TABLE_MOVES_90_CCW_LEFT_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '4 to 3'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited - 1'

        # history when right container picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_9_TABLE_MOVES_90_CCW_RIGHT_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '2 to 1'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited + 3'

        # history when container betweeen middle and right is picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_9_TABLE_MOVES_90_CCW_RIGHT_MID_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '7 to 6'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'opposite'

        # history when middle container is picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_9_TABLE_MOVES_90_CCW_MIDDLE_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '5 to 5'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited + 1'


    def test_calc_set_rotation_five_container_baited_starts_on_left(self):
        # 5 containers, turntable moves 90 degrees counterclockwise, container starting on 
        # left is baited
        # history when left container is picked
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SET_ROTATION_5_TEST_10_TABLE_MOVES_90_CCW)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_10_TABLE_MOVES_90_CCW_CORRECT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '4 to 3'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited'

        # history when container betweeen middle and left is picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_10_TABLE_MOVES_90_CCW_LEFT_MID_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '9 to 8'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited + 1'

        # history when right container picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_10_TABLE_MOVES_90_CCW_RIGHT_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '2 to 1'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'opposite'

        # history when container betweeen middle and right is picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_10_TABLE_MOVES_90_CCW_RIGHT_MID_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '7 to 6'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited + 3'

        # history when middle container is picked
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SET_ROTATION_5_TEST_10_TABLE_MOVES_90_CCW_MIDDLE_PICKED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_set_rotation()
        assert scorecard.get_set_rotation_opened_container_position_absolute() == '5 to 5'
        assert scorecard.get_set_rotation_opened_container_position_relative_to_baited() == 'baited + 2'


    def test_calc_shell_game(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SHELL_GAME_CROSS_BAITED_PICKED_DISPLACEMENT)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SHELL_GAME_CROSS_BAITED_PICKED_DISPLACEMENT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_shell_game()
        assert scorecard.get_shell_game_opened_container_position_relative_to_baited() == 'baited'
        assert scorecard.get_shell_game_opened_container() == '3 to 1'

        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SHELL_GAME_3_LATERAL_SUBSTITUTION_BAITED_PICKED_DISPLACEMENT)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SHELL_GAME_3_LATERAL_SUBSTITUTION_BAITED_PICKED_DISPLACEMENT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_shell_game()
        assert scorecard.get_shell_game_opened_container_position_relative_to_baited() == 'baited'
        assert scorecard.get_shell_game_opened_container() == '3 to 4'

        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SHELL_GAME_2_LATERAL_BAITED_PICKED_NO_DISPLACEMENT)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SHELL_GAME_2_LATERAL_BAITED_PICKED_NO_DISPLACEMENT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_shell_game()
        assert scorecard.get_shell_game_opened_container_position_relative_to_baited() == 'baited'
        assert scorecard.get_shell_game_opened_container() == '4 to 5'

        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SHELL_GAME_2_CROSS_CROSSED_PICKED_DISPLACEMENT)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SHELL_GAME_2_CROSS_CROSSED_PICKED_DISPLACEMENT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_shell_game()
        assert scorecard.get_shell_game_opened_container_position_relative_to_baited() == 'right'
        assert scorecard.get_shell_game_opened_container() == '3 to 3'

        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SHELL_GAME_3_LATERAL_SUBSTITUTION_SUBSTITUTED_PICKED_NO_DISPLACEMENT)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SHELL_GAME_3_LATERAL_SUBSTITUTION_SUBSTITUTED_PICKED_NO_DISPLACEMENT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_shell_game()
        assert scorecard.get_shell_game_opened_container_position_relative_to_baited() == 'middle'
        assert scorecard.get_shell_game_opened_container() == '3 to 4'

        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_UPDATED_SHELL_GAME_3_LATERAL_DISPLACEMENT)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_UPDATED_SHELL_GAME_3_LATERAL_DISPLACEMENT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_shell_game()
        assert scorecard.get_shell_game_opened_container_position_relative_to_baited() == 'opposite'
        assert scorecard.get_shell_game_opened_container() == '1 to 1'

        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_UPDATED_SHELL_GAME_3_CROSS_DISPLACEMENT)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_UPDATED_SHELL_GAME_3_CROSS_DISPLACEMENT_CORRECT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_shell_game()
        assert scorecard.get_shell_game_opened_container_position_relative_to_baited() == 'baited'
        assert scorecard.get_shell_game_opened_container() == '4 to 2'

        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_UPDATED_SHELL_GAME_3_CROSS_DISPLACEMENT)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_UPDATED_SHELL_GAME_3_CROSS_DISPLACEMENT_LEFT)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_shell_game()
        assert scorecard.get_shell_game_opened_container_position_relative_to_baited() == 'left'
        assert scorecard.get_shell_game_opened_container() == '1 to 1'

    def test_calc_door_opened_side(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_INTERACTIVE_COLLISION_DOOR_OPENED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_INTERACTIVE_COLLISION_DOOR_OPENED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_door_opened_side()
        assert scorecard.get_door_opened_side() == 'right'

        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_TRAJECTORY_DOOR_OPENED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_TRAJECTORY_DOOR_OPENED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_door_opened_side()
        assert scorecard.get_door_opened_side() == 'left'

        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SOLIDITY_DOOR_OPENED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SOLIDITY_DOOR_OPENED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_door_opened_side()
        assert scorecard.get_door_opened_side() == 'left'

        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_SUPPORT_RELATIONS_DOOR_OPENED)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_SUPPORT_RELATIONS_DOOR_OPENED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_door_opened_side()
        assert scorecard.get_door_opened_side() == 'middle'

    def test_calc_interacted_with_blob_first(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_INTERACTED_WITH_BLOB_FIRST_HOLES)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_INTERACTED_WITH_BLOB_FIRST_HOLES)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_interacted_with_blob_first()
        assert scorecard.get_interacted_with_blob_first() is False

        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_INTERACTED_WITH_BLOB_FIRST_LAVA)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_INTERACTED_WITH_BLOB_FIRST_LAVA)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_interacted_with_blob_first()
        assert scorecard.get_interacted_with_blob_first() is True

        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_INTERACTED_WITH_BLOB_FIRST_RAMPS)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_INTERACTED_WITH_BLOB_FIRST_RAMPS)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_interacted_with_blob_first()
        assert scorecard.get_interacted_with_blob_first() is True

    def test_pickup_non_target_mock_false_because_no_pickup(self):
        history = {'steps': [{
            'action': 'MoveAhead',
            'output': {
                'return_status': 'SUCCESSFUL',
                'resolved_object': None
            }
        }, {
            'action': 'MoveAhead',
            'output': {
                'return_status': 'OBSTRUCTED',
                'resolved_object': None
            }
        }]}
        scene = {
            'goal': {'category': 'retrieval', 'metadata': {'target': {'id': 'id_target'}}},
            'objects': [
                {'id': 'id_target', 'type': 'soccer_ball'},
                {'id': 'id_non_target', 'type': 'soccer_ball'}
            ]
        }
        scorecard = Scorecard(history, scene)
        scorecard.calc_pickup_non_target()
        assert scorecard.get_pickup_non_target() is False

    def test_pickup_non_target_mock_false_because_pickup_target(self):
        history = {'steps': [{
            'action': 'MoveAhead',
            'output': {
                'return_status': 'SUCCESSFUL',
                'resolved_object': None
            }
        }, {
            'action': 'PickupObject',
            'output': {
                'return_status': 'SUCCESSFUL',
                'resolved_object': 'id_target'
            }
        }]}
        scene = {
            'goal': {'category': 'retrieval', 'metadata': {'target': {'id': 'id_target'}}},
            'objects': [
                {'id': 'id_target', 'type': 'soccer_ball'},
                {'id': 'id_non_target', 'type': 'soccer_ball'}
            ]
        }
        scorecard = Scorecard(history, scene)
        scorecard.calc_pickup_non_target()
        assert scorecard.get_pickup_non_target() is False

    def test_pickup_non_target_mock_false_because_pickup_failed(self):
        history = {'steps': [{
            'action': 'MoveAhead',
            'output': {
                'return_status': 'SUCCESSFUL',
                'resolved_object': None
            }
        }, {
            'action': 'PickupObject',
            'output': {
                'return_status': 'NOT_VISIBLE',
                'resolved_object': 'id_non_target'
            }
        }]}
        scene = {
            'goal': {'category': 'retrieval', 'metadata': {'target': {'id': 'id_target'}}},
            'objects': [
                {'id': 'id_target', 'type': 'soccer_ball'},
                {'id': 'id_non_target', 'type': 'soccer_ball'}
            ]
        }
        scorecard = Scorecard(history, scene)
        scorecard.calc_pickup_non_target()
        assert scorecard.get_pickup_non_target() is False

    def test_pickup_non_target_mock_true(self):
        history = {'steps': [{
            'action': 'MoveAhead',
            'output': {
                'return_status': 'SUCCESSFUL',
                'resolved_object': None
            }
        }, {
            'action': 'PickupObject',
            'output': {
                'return_status': 'SUCCESSFUL',
                'resolved_object': 'id_non_target'
            }
        }]}
        scene = {
            'goal': {'category': 'retrieval', 'metadata': {'target': {'id': 'id_target'}}},
            'objects': [
                {'id': 'id_target', 'type': 'soccer_ball'},
                {'id': 'id_non_target', 'type': 'soccer_ball'}
            ]
        }
        scorecard = Scorecard(history, scene)
        scorecard.calc_pickup_non_target()
        assert scorecard.get_pickup_non_target() is True

    def test_pickup_non_target_mock_multi_retrieval_false(self):
        history = {'steps': [{
            'action': 'PickupObject',
            'output': {
                'return_status': 'SUCCESSFUL',
                'resolved_object': 'id_target_1'
            }
        }, {
            'action': 'PickupObject',
            'output': {
                'return_status': 'SUCCESSFUL',
                'resolved_object': 'id_target_2'
            }
        }]}
        scene = {
            'goal': {'category': 'multi retrieval', 'metadata': {'targets': [
                {'id': 'id_target_1'}, {'id': 'id_target_2'}
            ]}},
            'objects': [
                {'id': 'id_target_1', 'type': 'soccer_ball'},
                {'id': 'id_target_2', 'type': 'soccer_ball'},
                {'id': 'id_non_target', 'type': 'soccer_ball'}
            ]
        }
        scorecard = Scorecard(history, scene)
        scorecard.calc_pickup_non_target()
        assert scorecard.get_pickup_non_target() is False

    def test_pickup_non_target_mock_multi_retrieval_true(self):
        history = {'steps': [{
            'action': 'PickupObject',
            'output': {
                'return_status': 'SUCCESSFUL',
                'resolved_object': 'id_non_target'
            }
        }]}
        scene = {
            'goal': {'category': 'multi retrieval', 'metadata': {'targets': [
                {'id': 'id_target_1'}, {'id': 'id_target_2'}
            ]}},
            'objects': [
                {'id': 'id_target_1', 'type': 'soccer_ball'},
                {'id': 'id_target_2', 'type': 'soccer_ball'},
                {'id': 'id_non_target', 'type': 'soccer_ball'}
            ]
        }
        scorecard = Scorecard(history, scene)
        scorecard.calc_pickup_non_target()
        assert scorecard.get_pickup_non_target() is True

    def test_pickup_non_target_mock_multi_retrieval_ambiguous(self):
        history = {'steps': [{
            'action': 'PickupObject',
            'output': {
                'return_status': 'SUCCESSFUL',
                'resolved_object': 'non_id_target_1'
            }
        }, {
            'action': 'PickupObject',
            'output': {
                'return_status': 'SUCCESSFUL',
                'resolved_object': 'non_id_target_2'
            }
        }]}
        scene = {
            'goal': {'category': 'multi retrieval', 'metadata': {'targets': [
                {'id': 'id_target_1'}, {'id': 'id_target_2'}
            ]}},
            'objects': [
                {'id': 'id_target_1', 'type': 'soccer_ball'},
                {'id': 'id_target_2', 'type': 'soccer_ball'},
                {'id': 'id_non_target_1', 'type': 'soccer_ball'},
                {'id': 'id_non_target_2', 'type': 'soccer_ball'}
            ]
        }
        scorecard = Scorecard(history, scene)
        scorecard.calc_pickup_non_target()
        assert scorecard.get_pickup_non_target() is False

    def test_pickup_non_target_mock_no_target(self):
        history = {'steps': [{
            'action': 'Pass',
            'output': {
                'return_status': 'SUCCESSFUL'
            }
        }]}
        scene = {
            'goal': {'category': 'passive'},
            'objects': [
                {'id': 'id_non_target_1', 'type': 'soccer_ball'},
                {'id': 'id_non_target_2', 'type': 'soccer_ball'}
            ]
        }
        scorecard = Scorecard(history, scene)
        scorecard.calc_pickup_non_target()
        assert scorecard.get_pickup_non_target() is False

    def test_pickup_non_target_false_because_no_pickup(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_TOOL_CHOICE)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_TOOL_CHOICE_PICKUP_NOTHING)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_pickup_non_target()
        assert scorecard.get_pickup_non_target() is False

    def test_pickup_non_target_false_because_pickup_target(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_TOOL_CHOICE)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_TOOL_CHOICE_PICKUP_TARGET)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_pickup_non_target()
        assert scorecard.get_pickup_non_target() is False

    def test_pickup_non_target_false_because_pickup_failed(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_TOOL_CHOICE)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_TOOL_CHOICE_PICKUP_FAILED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_pickup_non_target()
        assert scorecard.get_pickup_non_target() is False

    def test_pickup_non_target_true(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_TOOL_CHOICE)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_TOOL_CHOICE_PICKUP_NON_TARGET)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_pickup_non_target()
        assert scorecard.get_pickup_non_target() is True

    def test_basic_tool_usage_stats(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_TOOL_USE)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_TOOL_USE)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_tool_usage()
        tool_usage = scorecard.get_tool_usage()
        expected = {'PushObject': 2, 'PullObject': 3, 'MoveObject': 2}
        assert tool_usage == expected

    def test_stepped_in_lava_false(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_TOOL_USE)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_TOOL_USE)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_stepped_in_lava()
        lava_step = scorecard.get_stepped_in_lava()
        assert lava_step is False

    def test_stepped_in_lava_true(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_LAVA_STEP)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_LAVA_STEP)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_stepped_in_lava()
        lava_step = scorecard.get_stepped_in_lava()
        assert lava_step is True

    def test_multi_tool_choice_stats_both_tools(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_MULTI_TOOL)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_MULTI_TOOL_BOTH_TOOLS_ROTATED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_tool_usage()
        tool_usage = scorecard.get_tool_usage()
        expected = {
            'PushObject_failed': 21, 
            'PushObject': 43, 
            'RotateObject': 3,
            'RotateObject_failed': 1, 
            'total_tools_used': 2, 
            'is_hooked_rotated': True, 
            'is_straight_rotated': True
        }
        assert tool_usage == expected


    def test_multi_tool_choice_stats_no_tools_used(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_MULTI_TOOL)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_MULTI_TOOL_NO_TOOLS_USED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_tool_usage()
        tool_usage = scorecard.get_tool_usage()
        expected = {
            'total_tools_used': 0,
            'is_hooked_rotated': False, 
            'is_straight_rotated': False
        }
        assert tool_usage == expected

    def test_multi_tool_choice_stats_straight_tool_rotated(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_MULTI_TOOL)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_MULTI_TOOL_RECT_ROTATED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_tool_usage()
        tool_usage = scorecard.get_tool_usage()
        expected = {
            'PushObject': 1,
            'RotateObject': 1,
            'total_tools_used': 1,
            'is_hooked_rotated': False, 
            'is_straight_rotated': True
        }
        assert tool_usage == expected

    def test_multi_tool_choice_stats_hooked_tool_rotated(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_MULTI_TOOL)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_MULTI_TOOL_HOOKED_ROTATED)
        scorecard = Scorecard(history_file, scene_file)
        scorecard.calc_tool_usage()
        tool_usage = scorecard.get_tool_usage()
        expected = {
            'PushObject_failed': 8,
            'PushObject': 31,
            'RotateObject_failed': 1,
            'RotateObject': 1,
            'total_tools_used': 2, 
            'is_hooked_rotated': True, 
            'is_straight_rotated': False
        }
        assert tool_usage == expected
