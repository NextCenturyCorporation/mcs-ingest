import logging
import unittest

import mcs_scene_ingest
from scorecard.scorecard import Scorecard
from scorecard.scorecard import get_lookpoint

TEST_SCENE_FILE_NAME = "occluders_0001_17_I1_debug.json"
TEST_HISTORY_FILE_NAME = "generator/SCENE_HISTORY/" + \
                         "india_0003_baseline_level1.json"
TEST_FOLDER = "tests"


class TestMcsScorecard(unittest.TestCase):

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

        # Looking back to right, down 30 so dist is sqrt(2)/2, but z is negative
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

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    unittest.main()
