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

TEST_SCENE_FILE_NAME = "occluders_0001_17_I1_debug.json"
TEST_HISTORY_FILE_NAME = "india_0003_baseline_level1.json"

TEST_SCENE_CONTAINER = "golf_0018_15_debug.json"
TEST_HISTORY_CONTAINER = "golf_0018_15_baseline.json"

TEST_SCENE_MOVING_TARGET = "alpha_0001_03_debug.json"
TEST_HISTORY_MOVING_TARGET_PASS = "alpha_0001_03_test_pass.json"
TEST_HISTORY_MOVING_TARGET_FAIL = "alpha_0001_03_test_fail.json"

TEST_SCENE_NO_TARGET = "juliett_0001_01_debug.json"
TEST_HISTORY_NO_TARGET = "test_eval_3-5_level2_baseline_juliett_0001_01.json"

TEST_FOLDER = "./tests/test_data"

# Hide all non-error log messages while running these unit tests.
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def create_mock_step(
        action: str = 'Pass',
        object_coords: dict = None,
        position: dict = None,
        receptacle_coords: dict = None,
        return_status: str = 'SUCCESSFUL',
        rotation: int = 0
) -> dict:
    return {
        'action': action,
        'output': {
            'position': position or {'x': 0, 'y': 0, 'z': 0},
            'return_status': return_status,
            'rotation': rotation
        },
        'params': {
            'objectImageCoords': object_coords or {'x': 0, 'y': 0},
            'receptacleObjectImageCoords': (
                receptacle_coords or {'x': 0, 'y': 0},
            )
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
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_FILE_NAME)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_FILE_NAME)
        scorecard = Scorecard(history_file, scene_file)
        scorecard_vals = scorecard.score_all()
        self.assertEqual(scorecard_vals["repeat_failed"], 0)
        self.assertEqual(scorecard_vals["revisits"], 1)
        logging.info(f"{scorecard_vals}")

    def test_get_lookpoint(self):
        import numpy as np
        import math

        # Not looking down, so no lookpoint
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
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_NO_TARGET)
        hist_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_NO_TARGET)
        target_id, x, z = find_target_loc_by_step(scene_file, hist_file["steps"][0])
        self.assertFalse(target_id, "Target should not exist, " +
                         f"but it does {x} {z}")

    def test_find_target_location_with_target(self):
        '''Test trying to find a target, when there is not one'''
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_MOVING_TARGET)
        hist_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_HISTORY_MOVING_TARGET_PASS)
        target_id, x, z = find_target_loc_by_step(scene_file, hist_file["steps"][0])
        if target_id is None:
            self.fail("Target not found")
        np.testing.assert_almost_equal(x, -3.654195547103882, err_msg="x location is wrong")
        np.testing.assert_almost_equal(z, 3.75, err_msg="Z location is wrong")

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
        repeat_failed = calc_repeat_failed([
            create_mock_step(action='MoveAhead', return_status='FAILED'),
            create_mock_step(action='MoveAhead', return_status='FAILED')
        ])
        self.assertEqual(repeat_failed, 0)

    def test_calc_repeat_failed_ignore_obstructed(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(action='MoveAhead', return_status='OBSTRUCTED'),
            create_mock_step(action='MoveAhead', return_status='OBSTRUCTED')
        ])
        self.assertEqual(repeat_failed, 0)

    def test_calc_repeat_failed_one_success(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200}
            )
        ])
        self.assertEqual(repeat_failed, 0)

    def test_calc_repeat_failed_one_failure(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                return_status='OUT_OF_REACH'
            )
        ])
        self.assertEqual(repeat_failed, 0)

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
        self.assertEqual(repeat_failed, 1)

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
        self.assertEqual(repeat_failed, 2)

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
        self.assertEqual(repeat_failed, 1)

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
        self.assertEqual(repeat_failed, 0)

    def test_calc_repeat_failed_two_failures_different_params(self):
        repeat_failed = calc_repeat_failed([
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 300, 'y': 200},
                return_status='OUT_OF_REACH'
            ),
            create_mock_step(
                action='PickupObject',
                object_coords={'x': 0, 'y': 0},
                return_status='OUT_OF_REACH'
            )
        ])
        self.assertEqual(repeat_failed, 0)

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
        self.assertEqual(repeat_failed, 0)

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
        self.assertEqual(repeat_failed, 0)

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
        self.assertEqual(repeat_failed, 0)

