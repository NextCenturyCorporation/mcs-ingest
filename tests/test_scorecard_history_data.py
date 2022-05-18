#
# Scorecard tests on scene history files
#
import json
import logging
import unittest

import mcs_scene_ingest
from scorecard import Scorecard

TEST_FOLDER = "./tests/test_data"

GROUND_TRUTH = f'{TEST_FOLDER}/ground_truth.json'

SCENE_FILE = 'india_0003_17_debug.json'
HIST_FILE = 'gen_repeat_failed_one.json'

TEST_SCENE_RAMP = "ramps_eval_5_ex_1.json"
TEST_HISTORY_RAMP_UP_DOWN = "ramps_all_moves.json"

# Hide all non-error log messages while running these unit tests.
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class TestMcsScorecard(unittest.TestCase):
    gt_tests = None

    @classmethod
    def setUpClass(cls) -> None:
        '''Read in ground truth file and store expected results'''

        cls.gt_tests = []

        with open(GROUND_TRUTH) as f:
            gt_data = json.load(f)
            cls.gt_tests = gt_data["ground_truth"]

    def test_move_toward(self):
        for gt_test in self.gt_tests:
            scene_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.get('scene_file'))
            history_file = mcs_scene_ingest.load_json_file(

                TEST_FOLDER, gt_test.get('history_file'))
            s = Scorecard(history_file, scene_file)
            not_moving = s.calc_not_moving_toward_object()
            gt_not_moving = gt_test.get('not_moving_toward', 0)
            self.assertEqual(gt_not_moving, not_moving,
                             f"Move twd error: {gt_test.get('history_file')}")

    def test_relook(self):
        for gt_test in self.gt_tests:
            scene_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.get('scene_file'))
            history_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.get('history_file'))
            s = Scorecard(history_file, scene_file)
            relooks = s.calc_relook()
            self.assertEqual(gt_test.get('relook', 0), relooks,
                             f"Relook error: {gt_test.get('history_file')}")

    def test_repeat_failed(self):
        for gt_test in self.gt_tests:
            scene_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.get('scene_file'))
            history_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.get('history_file'))
            s = Scorecard(history_file, scene_file)
            repeat_failed_dict = s.calc_repeat_failed()
            repeat_failed = repeat_failed_dict.get('total_repeat_failed', 0)
            self.assertEqual(
                gt_test.get('repeat_failed', 0),
                repeat_failed,
                f"Repeat failed error: {gt_test.get('history_file')}")

    def test_revisit(self):
        for gt_test in self.gt_tests:
            scene_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.get('scene_file'))
            history_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.get('history_file'))
            s = Scorecard(history_file, scene_file)
            revisit = s.calc_revisiting()
            self.assertEqual(gt_test.get('revisits', 0), revisit,
                             f"Revisit error: {gt_test.get('history_file')}")

    def test_unopenable(self):
        for gt_test in self.gt_tests:
            scene_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.get('scene_file'))
            history_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.get('history_file'))
            s = Scorecard(history_file, scene_file)
            unopenable = s.calc_open_unopenable()
            self.assertEqual(
                gt_test.get('unopenable', 0),
                unopenable.get('total_unopenable_attempts', 0),
                f"Unopenable error: {gt_test.get('history_file')}")

    def test_ramps(self):
        for gt_test in self.gt_tests:
            scene_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.get('scene_file'))
            history_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.get('history_file'))
            s = Scorecard(history_file, scene_file)
            ramp_actions = s.calc_ramp_actions()
            self.assertEqual(gt_test.get('ramp_up', 0),
                             ramp_actions.get('went_up', 0))
            self.assertEqual(gt_test.get('ramp_down', 0),
                             ramp_actions.get('went_down', 0))
            self.assertEqual(gt_test.get('ramp_up_abandoned', 0),
                             ramp_actions.get('went_up_abandoned', 0))
            self.assertEqual(gt_test.get('ramp_down_abandoned', 0),
                             ramp_actions.get('went_down_abandoned', 0))
            self.assertEqual(gt_test.get('ramp_fall', 0),
                             ramp_actions.get('ramp_fell_off', 0))

    def test_tool_usage(self):
        for gt_test in self.gt_tests:
            scene_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.get('scene_file'))
            history_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.get('history_file'))
            s = Scorecard(history_file, scene_file)
            tool_usage_data = s.calc_tool_usage()
            for tool_key in tool_usage_data:
                self.assertEqual(
                    gt_test.get(tool_key, 0),
                    tool_usage_data.get(tool_key, 0),
                    f"Tool usage error: {tool_key} " +
                    f"{gt_test.get('history_file')}")

    def test_platform_side(self):
        for gt_test in self.gt_tests:
            scene_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.get('scene_file'))
            history_file = mcs_scene_ingest.load_json_file(
                TEST_FOLDER, gt_test.get('history_file'))
            s = Scorecard(history_file, scene_file)
            platform_side = s.calc_correct_platform_side()
            self.assertEqual(
                gt_test.get('platform_side', None),
                platform_side.get('platform_side'),
                f"{gt_test.get('history_file')}")

    def test_get_scorecard_dict(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, SCENE_FILE)
        history_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, HIST_FILE)
        s = Scorecard(history_file, scene_file)
        scorecard_dict = s.score_all()
        repeat = scorecard_dict.get('repeat_failed')
        self.assertEqual(repeat.get('total_repeat_failed'), 1)
        self.assertEqual(repeat.get('d06bc6e8-3ab2-4956-8dee-c46e4357c73b'), 1)
