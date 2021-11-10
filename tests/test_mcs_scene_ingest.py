import logging
import unittest

import mcs_scene_ingest

from pymongo import MongoClient

TEST_SCENE_FILE_NAME = "test_juliett_0001_01_debug.json"
TEST_HISTORY_FILE_NAME = "test_eval_3-5_level2_baseline_juliett_0001_01.json"
TEST_INTERACTIVE_SCENE_FILE_NAME = "occluders_0001_17_I1_debug.json"
TEST_INTERACTIVE_HISTORY_FILE_NAME = "occluders_0001_17_baseline.json"
TEST_FOLDER = "tests"


class TestMcsSceneIngest(unittest.TestCase):

    def test_load_json_file(self):
        scene_file = mcs_scene_ingest.load_json_file(
            TEST_FOLDER, TEST_SCENE_FILE_NAME)
        self.assertEqual(scene_file["name"], "juliett_0001_01")
        self.assertEqual(scene_file["debug"]["training"], False)

    def test_delete_keys_from_scene(self):
        test_scene = {
            "name": "test",
            "version": 2,
            "image": "image_to_delete",
            "debug": {
                "sequenceNumber": 1,
                "hypercubeNumber": 5,
                "sceneNumber": 100
            }
        }

        scene_removed_keys = mcs_scene_ingest.delete_keys_from_scene(
            test_scene, mcs_scene_ingest.KEYS_TO_DELETE)
        self.assertEqual(scene_removed_keys["name"], "test")
        self.assertEqual(scene_removed_keys["version"], 2)
        self.assertEqual(scene_removed_keys.get("image"), None)
        self.assertEqual(scene_removed_keys.get("debug"), None)

    def test_find_scene_files(self):
        scene_files = mcs_scene_ingest.find_scene_files(TEST_FOLDER)
        self.assertEqual(len(scene_files), 5)
        self.assertTrue(TEST_SCENE_FILE_NAME in scene_files)

    def test_build_scene_item(self):
        scene = mcs_scene_ingest.build_scene_item(
            TEST_SCENE_FILE_NAME, TEST_FOLDER, None)
        self.assertEqual(scene["eval"], "Evaluation 3.5 Scenes")
        self.assertEqual(scene["test_num"], 1)
        self.assertEqual(scene.get("debug"), None)

    def test_determine_evaluation_hist_name(self):
        eval_name = mcs_scene_ingest.determine_evaluation_hist_name(
            "Eval3", "eval3.5")
        self.assertEqual(eval_name, "Eval3")
        eval_name = mcs_scene_ingest.determine_evaluation_hist_name(
            None, "eval3.5")
        self.assertEqual(eval_name, "eval3.5")
        eval_name = mcs_scene_ingest.determine_evaluation_hist_name(
            None, "eval_3-5")
        self.assertEqual(eval_name, "Evaluation 3.5 Results")

    def test_determine_team_mapping_name(self):
        team_name = mcs_scene_ingest.determine_team_mapping_name("ibm")
        self.assertEqual(team_name, "IBM")
        team_name = mcs_scene_ingest.determine_team_mapping_name("mit")
        self.assertEqual(team_name, "IBM-MIT-Harvard-Stanford")

    def test_build_history_item(self):
        client = MongoClient(
            'mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
        history_item = mcs_scene_ingest.build_history_item(
            TEST_HISTORY_FILE_NAME, TEST_FOLDER, "eval_4",
            "cora", TEST_FOLDER, ".json", client, "mcs")
        logging.info(f"{history_item}")

    def test_build_interactive_history_item(self):
        '''Generates history item for an interactive, which follows
        a different code path (and includes scorecard)'''
        client = MongoClient(
            'mongodb://mongomcs:mongomcspassword@localhost:27017/mcs')
        history_item = mcs_scene_ingest.build_history_item(
            TEST_INTERACTIVE_HISTORY_FILE_NAME, TEST_FOLDER,
            "eval_4", "cora", TEST_FOLDER, ".json", client, "mcs")
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
            mcs_scene_ingest.reorientation_calculate_corners(test_scene))
        self.assertEqual(len(incorrect_corners), 3)
        self.assertEqual(len(correct_corners), 1)
        self.assertTrue("front_right" not in incorrect_corners)
        self.assertTrue("front_right" in correct_corners)

        test_scene["goal"]["sceneInfo"]["ambiguous"] = True
        test_scene["goal"]["sceneInfo"]["corner"] = "front_left"

        (incorrect_corners, correct_corners) = (
            mcs_scene_ingest.reorientation_calculate_corners(test_scene))
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
            mcs_scene_ingest.reorientation_calculate_corners(test_scene))

        corner_order = mcs_scene_ingest.check_agent_to_corner_position(
            position, incorrect_corners, correct_corners, corner_order)
        reorientation_score = (
            mcs_scene_ingest.calculate_reorientation_score(corner_order, 0))
        self.assertEqual(reorientation_score, 1)

        corner_order = []
        position = {"x": 0, "z": 0}
        corner_order = mcs_scene_ingest.check_agent_to_corner_position(
            position, incorrect_corners, correct_corners, corner_order)
        reorientation_score = (
            mcs_scene_ingest.calculate_reorientation_score(corner_order, 0))
        self.assertEqual(reorientation_score, 0)

    def test_update_agency_scoring_both_none(self):
        history_item_1 = {'score': {'classification': None}}
        history_item_2 = {'score': {'classification': None}}
        mcs_scene_ingest.update_agency_scoring(history_item_1, history_item_2)
        
        self.assertEqual(history_item_1['score']['score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score_worth'], 1)
        self.assertEqual(history_item_1['score']['score_description'], 'Incorrect')

        self.assertEqual(history_item_2['score']['score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score_worth'], 0)
        self.assertEqual(history_item_2['score']['score_description'], 'Incorrect')

    def test_update_agency_scoring_item1_none(self):
        history_item_1 = {'score': {'classification': None}}
        history_item_2 = {'score': {'classification': 0.999}}
        mcs_scene_ingest.update_agency_scoring(history_item_1, history_item_2)
        
        self.assertEqual(history_item_1['score']['score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score_worth'], 1)
        self.assertEqual(history_item_1['score']['score_description'], 'Incorrect')

        self.assertEqual(history_item_2['score']['score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score_worth'], 0)
        self.assertEqual(history_item_2['score']['score_description'], 'Incorrect')

    def test_update_agency_scoring_item2_none(self):
        history_item_1 = {'score': {'classification': 0.999}}
        history_item_2 = {'score': {'classification': None}}
        mcs_scene_ingest.update_agency_scoring(history_item_1, history_item_2)
        
        self.assertEqual(history_item_1['score']['score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score'], 0)
        self.assertEqual(history_item_1['score']['weighted_score_worth'], 1)
        self.assertEqual(history_item_1['score']['score_description'], 'Incorrect')

        self.assertEqual(history_item_2['score']['score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score'], 0)
        self.assertEqual(history_item_2['score']['weighted_score_worth'], 0)
        self.assertEqual(history_item_2['score']['score_description'], 'Incorrect')

    def test_update_agency_scoring_item1_lower_score(self):
        history_item_1 = {'score': {'classification': 0.888}}
        history_item_2 = {'score': {'classification': 0.999}}
        mcs_scene_ingest.update_agency_scoring(history_item_1, history_item_2)
        
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
        mcs_scene_ingest.update_agency_scoring(history_item_1, history_item_2)
        
        self.assertEqual(history_item_1['score']['score'], 1)
        self.assertEqual(history_item_1['score']['weighted_score'], 1)
        self.assertEqual(history_item_1['score']['weighted_score_worth'], 1)
        self.assertEqual(history_item_1['score']['score_description'], 'Correct')

        self.assertEqual(history_item_2['score']['score'], 1)
        self.assertEqual(history_item_2['score']['weighted_score'], 1)
        self.assertEqual(history_item_2['score']['weighted_score_worth'], 0)
        self.assertEqual(history_item_2['score']['score_description'], 'Correct')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    unittest.main()
