#
# Scorecard tests on scene history files
#
import logging
import unittest
from dataclasses import dataclass

import mcs_scene_ingest
from scorecard import Scorecard

TEST_FOLDER = "./tests/test_data"

GROUND_TRUTH = f'{TEST_FOLDER}/ground_truth.txt'

# Hide all non-error log messages while running these unit tests.
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@dataclass
class GT_Test:
    scene_file: str
    history_file: str
    num_revisits: int
    num_unopenable: int
    num_relook: int
    num_notmovetwd: int
    num_repeatfailed: int


class TestMcsScorecard(unittest.TestCase):
    gt_tests = None

    @classmethod
    def setUpClass(cls) -> None:

        cls.gt_tests = []

        '''Read in ground truth file and store expected results'''
        with open(GROUND_TRUTH) as f:
            lines = f.readlines()
            for line in lines:
                if line[0] == "#" or len(line.strip()) == 0:
                    continue
                vals = line.split()

                scene_filepath = vals[0].strip()
                history_filepath = vals[1].strip()

                gt_revisits = int(vals[2].strip())
                gt_unopenable = int(vals[3].strip())
                gt_relook = int(vals[4].strip())
                gt_not_moving_towards = int(vals[5].strip())
                gt_repeat_failed = int(vals[6].strip())

                gt_test = GT_Test(scene_filepath,
                                  history_filepath,
                                  gt_revisits,
                                  gt_unopenable,
                                  gt_relook,
                                  gt_not_moving_towards,
                                  gt_repeat_failed)
                cls.gt_tests.append(gt_test)

    def test_move_toward(self):
        for gt_test in self.gt_tests:
            scene_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.scene_file)
            history_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.history_file)
            s = Scorecard(history_file, scene_file)
            not_moving = s.calc_not_moving_toward_object()
            self.assertEqual(gt_test.num_notmovetwd, not_moving,
                             f"Move twd error: {gt_test.history_file}")

    def test_relook(self):
        for gt_test in self.gt_tests:
            scene_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.scene_file)
            history_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.history_file)
            s = Scorecard(history_file, scene_file)
            relooks = s.calc_relook()
            self.assertEqual(gt_test.num_relook, relooks,
                             f"Relook error: {gt_test.history_file}")

    def test_repeat_failed(self):
        for gt_test in self.gt_tests:
            scene_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.scene_file)
            history_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.history_file)
            s = Scorecard(history_file, scene_file)
            repeat_failed = s.calc_repeat_failed()
            self.assertEqual(gt_test.num_repeatfailed, repeat_failed,
                             f"Repeat failed error: {gt_test.history_file}")

    def test_revisit(self):
        for gt_test in self.gt_tests:
            scene_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.scene_file)
            history_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.history_file)
            s = Scorecard(history_file, scene_file)
            revisit = s.calc_revisiting()
            self.assertEqual(gt_test.num_revisits, revisit,
                             f"Revisit error: {gt_test.history_file}")

    def test_unopenable(self):
        for gt_test in self.gt_tests:
            scene_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.scene_file)
            history_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.history_file)
            s = Scorecard(history_file, scene_file)
            unopenable = s.calc_open_unopenable()
            self.assertEqual(gt_test.num_unopenable, unopenable,
                             f"Unopenable error: {gt_test.history_file}")
