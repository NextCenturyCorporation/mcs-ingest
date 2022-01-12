import logging
import unittest

import mcs_history_ingest

from pymongo import MongoClient

TEST_HISTORY_FILE_NAME = "test_eval_3-5_level2_baseline_juliett_0001_01.json"
TEST_INTERACTIVE_HISTORY_FILE_NAME = "occluders_0001_17_baseline.json"
TEST_FOLDER = "tests"


class TestMcsHistoryIngest(unittest.TestCase):

    def test_build_history_item(self):
        client = MongoClient(
            'mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
        history_item = mcs_history_ingest.build_history_item(
            TEST_HISTORY_FILE_NAME, TEST_FOLDER, "eval_4",
            "cora", TEST_FOLDER, ".json", client, "mcs", ignore_keys=True)
        logging.info(f"{history_item}")

    def test_build_interactive_history_item(self):
        '''Generates history item for an interactive, which follows
        a different code path (and includes scorecard)'''
        client = MongoClient(
            'mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
        history_item = mcs_history_ingest.build_history_item(
            TEST_INTERACTIVE_HISTORY_FILE_NAME, TEST_FOLDER,
            "eval_4", "cora", TEST_FOLDER, ".json", client, "mcs",
            ignore_keys=True)
        logging.info(f"{history_item}")

    def test_reorientation_calculate_corners(self):
        test_scene = {
            "goal": {
                "sceneInfo": {
                    "ambiguous": False,
                    "corner": "front_right"
                }
            }
        }

        (incorrect_corners, correct_corners) = (
            mcs_history_ingest.reorientation_calculate_corners(test_scene))
        self.assertEqual(len(incorrect_corners), 3)
        self.assertEqual(len(correct_corners), 1)
        self.assertTrue("front_right" not in incorrect_corners)
        self.assertTrue("front_right" in correct_corners)

        test_scene["goal"]["sceneInfo"]["ambiguous"] = True
        test_scene["goal"]["sceneInfo"]["corner"] = "front_left"

        (incorrect_corners, correct_corners) = (
            mcs_history_ingest.reorientation_calculate_corners(test_scene))
        self.assertEqual(len(incorrect_corners), 2)
        self.assertEqual(len(correct_corners), 2)
        self.assertTrue("front_left" not in incorrect_corners)
        self.assertTrue("back_right" not in incorrect_corners)
        self.assertTrue("back_right" in correct_corners)

    def test_check_agent_to_corner_position(self):
        test_scene = {
            "goal": {
                "sceneInfo": {
                    "ambiguous": False,
                    "corner": "front_right"
                }
            }
        }

        corner_order = []
        position = {"x": 5.5, "z": 3.9}
        (incorrect_corners, correct_corners) = (
            mcs_history_ingest.reorientation_calculate_corners(test_scene))

        corner_order = mcs_history_ingest.check_agent_to_corner_position(
            position, incorrect_corners, correct_corners, corner_order)
        reorientation_score = (
            mcs_history_ingest.calculate_reorientation_score(corner_order, 0))
        self.assertEqual(reorientation_score, 1)

        corner_order = []
        position = {"x": 0, "z": 0}
        corner_order = mcs_history_ingest.check_agent_to_corner_position(
            position, incorrect_corners, correct_corners, corner_order)
        reorientation_score = (
            mcs_history_ingest.calculate_reorientation_score(corner_order, 0))
        self.assertEqual(reorientation_score, 0)

    def test_update_agency_scoring_both_none(self):
        history_item_1 = {'score': {'classification': None}}
        history_item_2 = {'score': {'classification': None}}
        mcs_history_ingest.update_agency_scoring(history_item_1, history_item_2)
        
        self.assertEqual(history_item_1['score']['score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score_worth'], 1)
        self.assertEqual(history_item_1['score']['score_description'], 'No answer')

        self.assertEqual(history_item_2['score']['score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score_worth'], 0)
        self.assertEqual(history_item_2['score']['score_description'], 'No answer')

    def test_update_agency_scoring_item1_none(self):
        history_item_1 = {'score': {'classification': None}}
        history_item_2 = {'score': {'classification': 0.999}}
        mcs_history_ingest.update_agency_scoring(history_item_1, history_item_2)
        
        self.assertEqual(history_item_1['score']['score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score_worth'], 0)
        self.assertEqual(history_item_1['score']['score_description'], 'No answer')

        self.assertEqual(history_item_2['score']['score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score_worth'], 1)
        self.assertEqual(history_item_2['score']['score_description'], 'Incorrect')

    def test_update_agency_scoring_item2_none(self):
        history_item_1 = {'score': {'classification': 0.999}}
        history_item_2 = {'score': {'classification': None}}
        mcs_history_ingest.update_agency_scoring(history_item_1, history_item_2)
        
        self.assertEqual(history_item_1['score']['score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score_worth'], 1)
        self.assertEqual(history_item_1['score']['score_description'], 'Incorrect')

        self.assertEqual(history_item_2['score']['score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score_worth'], 0)
        self.assertEqual(history_item_2['score']['score_description'], 'No answer')

    def test_update_agency_scoring_item1_lower_score(self):
        history_item_1 = {'score': {'classification': 0.888}}
        history_item_2 = {'score': {'classification': 0.999}}
        mcs_history_ingest.update_agency_scoring(history_item_1, history_item_2)
        
        self.assertEqual(history_item_1['score']['score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score_worth'], 1)
        self.assertEqual(history_item_1['score']['score_description'], 'Incorrect')

        self.assertEqual(history_item_2['score']['score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score_worth'], 0)
        self.assertEqual(history_item_2['score']['score_description'], 'Incorrect')

    def test_update_agency_scoring_item1_higher_score(self):
        history_item_1 = {'score': {'classification': 0.999}}
        history_item_2 = {'score': {'classification': 0.888}}
        mcs_history_ingest.update_agency_scoring(history_item_1, history_item_2)
        
        self.assertEqual(history_item_1['score']['score'], 1)
        self.assertEqual(history_item_1['score']['weighted_score'], 1)
        self.assertEqual(history_item_1['score']['weighted_score_worth'], 1)
        self.assertEqual(history_item_1['score']['score_description'], 'Correct')

        self.assertEqual(history_item_2['score']['score'], 1)
        self.assertEqual(history_item_2['score']['weighted_score'], 1)
        self.assertEqual(history_item_2['score']['weighted_score_worth'], 0)
        self.assertEqual(history_item_2['score']['score_description'], 'Correct')

    def test_update_agency_scoring_item1_failure(self):
        history_item_1 = {'score': {'classification': ''}}
        history_item_2 = {'score': {'classification': 0.888}}
        mcs_history_ingest.update_agency_scoring(history_item_1, history_item_2)
        
        self.assertEqual(history_item_1['score']['score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score_worth'], 0)
        self.assertEqual(history_item_1['score']['score_description'], 'No answer')

        self.assertEqual(history_item_2['score']['score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score_worth'], 1)
        self.assertEqual(history_item_2['score']['score_description'], 'Incorrect')

    def test_update_agency_scoring_item2_failure(self):
        history_item_1 = {'score': {'classification': 0.999}}
        history_item_2 = {'score': {'classification': ''}}
        mcs_history_ingest.update_agency_scoring(history_item_1, history_item_2)
        
        self.assertEqual(history_item_1['score']['score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score_worth'], 1)
        self.assertEqual(history_item_1['score']['score_description'], 'Incorrect')

        self.assertEqual(history_item_2['score']['score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score_worth'], 0)
        self.assertEqual(history_item_2['score']['score_description'], 'No answer')

    def test_update_agency_scoring_both_item_failure(self):
        history_item_1 = {'score': {'classification': ''}}
        history_item_2 = {'score': {'classification': ''}}
        mcs_history_ingest.update_agency_scoring(history_item_1, history_item_2)
        
        self.assertEqual(history_item_1['score']['score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score_worth'], 1)
        self.assertEqual(history_item_1['score']['score_description'], 'No answer')

        self.assertEqual(history_item_2['score']['score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score_worth'], 0)
        self.assertEqual(history_item_2['score']['score_description'], 'No answer')

    def test_process_score_correct(self):
        history_item = {
            'category': 'passive',
            'test_type': 'intuitive physics',
            'score': {'classification': '1'}
        }
        scene = {'goal': {'answer': {'choice': 'plausible'}}}
        history_item["score"] = mcs_history_ingest.process_score(
            history_item, scene, False, False, None, False, None, None)

        self.assertEqual(history_item['score']['score'], 1)
        self.assertEqual(history_item['score']['score_description'], 'Correct')

    def test_process_score_incorrect(self):
        history_item = {
            'category': 'passive',
            'test_type': 'intuitive physics',
            'score': {'classification': '0'}
        }
        scene = {'goal': {'answer': {'choice': 'plausible'}}}
        history_item["score"] = mcs_history_ingest.process_score(
            history_item, scene, False, False, None, False, None, None)

        self.assertEqual(history_item['score']['score'], 0)
        self.assertEqual(history_item['score']['score_description'], 'Incorrect')

    def test_process_score_failure(self):
        history_item = {
            'category': 'passive',
            'test_type': 'intuitive physics',
            'score': {'classification': ''}
        }
        scene = {'goal': {'answer': {'choice': 'plausible'}}}
        history_item["score"] = mcs_history_ingest.process_score(
            history_item, scene, False, False, None, False, None, None)

        self.assertEqual(history_item['score']['score'], 0)
        self.assertEqual(history_item['score']['weighted_score'], 0)
        self.assertEqual(history_item['score']['weighted_score_worth'], 0)
        self.assertEqual(history_item['score']['score_description'], 'No answer')


    def test_determine_evaluation_hist_name(self):
        eval_name = mcs_history_ingest.determine_evaluation_hist_name(
            "Eval3", "eval3.5")
        self.assertEqual(eval_name, "Eval3")
        eval_name = mcs_history_ingest.determine_evaluation_hist_name(
            None, "eval3.5")
        self.assertEqual(eval_name, "eval3.5")
        eval_name = mcs_history_ingest.determine_evaluation_hist_name(
            None, "eval_3-5")
        self.assertEqual(eval_name, "Evaluation 3.5 Results")

    def test_determine_team_mapping_name(self):
        team_name = mcs_history_ingest.determine_team_mapping_name("ibm")
        self.assertEqual(team_name, "IBM")
        team_name = mcs_history_ingest.determine_team_mapping_name("mit")
        self.assertEqual(team_name, "IBM-MIT-Harvard-Stanford")
        