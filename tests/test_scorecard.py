import unittest
import mcs_scene_ingest
from scorecard.scorecard import Scorecard

TEST_SCENE_FILE_NAME = "occluders_0001_17_I1_debug.json"
TEST_HISTORY_FILE_NAME = "generator/SCENE_HISTORY/india_0003_baseline_level1.json"
TEST_FOLDER = "tests"
TEST_FOLDER = "/home/clark/work/mcs/mcs-ingest/tests"

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
        print(f"{scorecard_vals}")


if __name__ == '__main__':
    unittest.main()
