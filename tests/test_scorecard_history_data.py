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

SCENE_FILE = 'india_0003_17_debug.json'
HIST_FILE = 'gen_repeat_failed_one.json'

TEST_SCENE_RAMP = "ramps_eval_5_ex_1.json"
TEST_HISTORY_RAMP_UP_DOWN = "ramps_all_moves.json"

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
    num_ramp_up: int
    num_ramp_down: int
    num_ramp_up_abandoned: int
    num_ramp_down_abandoned: int
    num_ramp_fell_off: int
    num_torques: int
    num_pushes: int
    num_pulles: int
    num_rotates: int
    num_moves: int


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
                gt_ramp_up = int(vals[7].strip())
                gt_ramp_down = int(vals[8].strip())
                gt_ramp_up_abandoned = int(vals[9].strip())
                gt_ramp_down_abandoned = int(vals[10].strip())
                gt_ramp_fell_off = int(vals[11].strip())

                gt_torques = int(vals[12].strip())
                gt_pushes = int(vals[13].strip())
                gt_pulls = int(vals[14].strip())
                gt_rotates = int(vals[15].strip())
                gt_moves = int(vals[16].strip())

                gt_test = GT_Test(scene_filepath,
                                  history_filepath,
                                  gt_revisits,
                                  gt_unopenable,
                                  gt_relook,
                                  gt_not_moving_towards,
                                  gt_repeat_failed,
                                  gt_ramp_up,
                                  gt_ramp_down,
                                  gt_ramp_up_abandoned,
                                  gt_ramp_down_abandoned,
                                  gt_ramp_fell_off,
                                  gt_torques,
                                  gt_pushes,
                                  gt_pulls,
                                  gt_rotates,
                                  gt_moves)
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
            repeat_failed_dict = s.calc_repeat_failed()
            repeat_failed = repeat_failed_dict['total_repeat_failed']
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
            self.assertEqual(gt_test.num_unopenable,
                             unopenable['total_unopenable_attempts'],
                             f"Unopenable error: {gt_test.history_file}")

    def test_ramps(self):
        for gt_test in self.gt_tests:
            scene_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.scene_file)
            history_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.history_file)
            s = Scorecard(history_file, scene_file)
            ramp_actions = s.calc_ramp_actions()
            self.assertEqual(gt_test.num_ramp_up,
                             ramp_actions['went_up'])
            self.assertEqual(gt_test.num_ramp_down,
                             ramp_actions['went_down'])
            self.assertEqual(gt_test.num_ramp_up_abandoned,
                             ramp_actions['went_up_abandoned'])
            self.assertEqual(gt_test.num_ramp_down_abandoned,
                             ramp_actions['went_down_abandoned'])
            self.assertEqual(gt_test.num_ramp_fell_off,
                             ramp_actions['ramp_fell_off'])

    def test_torques(self):
        for gt_test in self.gt_tests:
            scene_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.scene_file)
            history_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.history_file)
            s = Scorecard(history_file, scene_file)
            torque_data = s.calc_torques()
            self.assertEqual(gt_test.num_torques,
                             torque_data['TorqueObject'],
                             f"Unopenable error: {gt_test.history_file}")

    def test_get_scorecard_dict(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, SCENE_FILE)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, HIST_FILE)
        s = Scorecard(history_file, scene_file)
        scorecard_dict = s.score_all()
        repeat = scorecard_dict['repeat_failed']
        self.assertEqual(repeat['total_repeat_failed'], 1)
        self.assertEqual(repeat['d06bc6e8-3ab2-4956-8dee-c46e4357c73b'], 1)
