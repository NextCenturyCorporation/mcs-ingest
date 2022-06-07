from enum import auto
import time
import unittest
import warnings

import docker
from pymongo import MongoClient

import mcs_history_ingest
import mcs_scene_ingest

TEST_HISTORY_FILE_NAME = "test_data/test_eval_3-5_level2_baseline_juliett_0001_01.json"
TEST_SCENE_FILE_NAME = "test_data/test_juliett_0001_01_debug.json"
TEST_INTERACTIVE_HISTORY_FILE_NAME = "test_data/occluders_0001_17_baseline.json"
TEST_INTERACTIVE_SCENE_FILE = "test_data/occluders_0001_17_I1_debug.json"
TEST_FOLDER = "tests"


class TestMcsHistoryIngestMongo(unittest.TestCase):
    '''Test database functionality of mcs_history_ingest using docker/mongo'''

    mongo_client = None
    mongo_host_port = 27027

    @classmethod
    def create_mongo_container(cls, docker_client, api_client, timeout=60):
        '''Helper method to create the mongodb container'''
        mongo_container = docker_client.containers.run(
            'mongo:latest',
            ports={27017: cls.mongo_host_port},
            healthcheck={
                "Test": 'mongo --eval \'db.runCommand("ping").ok\' localhost:27017/test --quiet',
                "Interval": 1_000_000 * 1_000,
            },
            remove=True,
            detach=True,
        )

        health = None
        max_time = time.time() + timeout
        while health != "healthy" and (time.time() < max_time):
            inspection = api_client.inspect_container(mongo_container.id)
            health = inspection["State"]["Health"]["Status"]
            time.sleep(1)
        # TODO health check could reach max_time and still be unhealthy
        return mongo_container

    @classmethod
    def setUpClass(cls):
        '''Start the mongo docker container'''
        # connect to docker daemon
        cls.docker_client = docker.from_env()
        # create low-level API client for health checks
        cls.api_client = docker.APIClient(
            base_url="unix://var/run/docker.sock")
        cls.mongo_container = cls.create_mongo_container(
            cls.docker_client,
            cls.api_client)
        cls.mongo_client = MongoClient(host="localhost", port=cls.mongo_host_port)

    @classmethod
    def tearDownClass(cls) -> None:
        '''Stop the docker container and close docker connections'''
        cls.mongo_container.stop()
        cls.docker_client.close()
        cls.api_client.close()

    def setUp(self):
        '''Create the client and insert a single document'''
        warnings.simplefilter('ignore', category=ResourceWarning)
        self.mongo_client = MongoClient(host='localhost', port=self.mongo_host_port)
        mcs_scene_ingest.automated_scene_ingest_file(
            file_name=TEST_SCENE_FILE_NAME,
            folder=TEST_FOLDER,
            db_string="mcs",
            client=self.mongo_client)
        mcs_scene_ingest.automated_scene_ingest_file(
            file_name=TEST_INTERACTIVE_SCENE_FILE,
            folder=TEST_FOLDER,
            db_string="mcs",
            client=self.mongo_client)
        mcs_history_ingest.automated_history_ingest_file(
            history_file=TEST_HISTORY_FILE_NAME,
            folder=TEST_FOLDER,
            db_string="mcs",
            client=self.mongo_client)

    def tearDown(self):
        '''Drop the database and close the connection'''
        self.mongo_client.drop_database('mcs')
        self.mongo_client.close()

    def test_true(self):
        self.assertTrue(True)

    def test_build_history_item(self):
        history_item = mcs_history_ingest.build_history_item(
            TEST_HISTORY_FILE_NAME, TEST_FOLDER,
            self.mongo_client, "mcs")
        self.assertIsNotNone(history_item)
        self.assertIsNotNone(history_item["slices"])

    def test_build_interactive_history_item(self):
        '''Generates history item for an interactive, which follows
        a different code path (and includes scorecard)'''
        history_item = mcs_history_ingest.build_history_item(
            TEST_INTERACTIVE_HISTORY_FILE_NAME, TEST_FOLDER,
            self.mongo_client, "mcs")
        self.assertIsNotNone(history_item)
        self.assertTrue(history_item["target_is_visible_at_start"])


class TestMcsHistoryIngest(unittest.TestCase):

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
        self.assertEqual(history_item['score']['score_description'],
                         'No answer')

    def test_determine_evaluation_hist_name(self):
        eval_name = mcs_history_ingest.determine_evaluation_hist_name(
            "eval3.5")
        self.assertEqual(eval_name, "eval3.5")
        eval_name = mcs_history_ingest.determine_evaluation_hist_name(
            "eval_3-5")
        self.assertEqual(eval_name, "Evaluation 3.5 Results")

    def test_determine_team_mapping_name(self):
        team_name = mcs_history_ingest.determine_team_mapping_name("ibm")
        self.assertEqual(team_name, "IBM")
        team_name = mcs_history_ingest.determine_team_mapping_name("mit")
        self.assertEqual(team_name, "IBM-MIT-Harvard-Stanford")

    def test_ignored_spatial_elimination_scenes(self):
        test_scene = {
            "goal": {
                "sceneInfo": {
                    "tertiaryType": "spatial elimination"
                }
            }
        }

        history_item = {
            'category': 'interactive',
            'test_type': 'retrieval',
            'category_type': 'spatial elimination',
            'scene_goal_id': 'A3',
            'score': {
                'classification': '1',
                'score': 1,
                'weighted_score': 1,
                'weighted_score_worth': 1,
                'confidence': 1,
                'weighted_confidence': 1
            }
        }
        history_item["score"] = mcs_history_ingest.process_score(
            history_item, test_scene, True, False, None, False, None, None)
        self.assertEqual(history_item['score']['score'], 1)
        self.assertEqual(history_item['score']['weighted_score'], 0)
        self.assertEqual(history_item['score']['weighted_score_worth'], 0)
        self.assertEqual(history_item['score']['weighted_confidence'], 0)

        history_item = {
            'category': 'interactive',
            'test_type': 'retrieval',
            'category_type': 'spatial elimination',
            'scene_goal_id': 'C4',
            'score': {
                'classification': '1',
                'score': 1,
                'weighted_score': 1,
                'weighted_score_worth': 1,
                'confidence': 1,
                'weighted_confidence': 1
            }
        }
        history_item["score"] = mcs_history_ingest.process_score(
            history_item, test_scene, True, False, None, False, None, None)
        self.assertEqual(history_item['score']['score'], 1)
        self.assertEqual(history_item['score']['weighted_score'], 0)
        self.assertEqual(history_item['score']['weighted_score_worth'], 0)
        self.assertEqual(history_item['score']['weighted_confidence'], 0)

        history_item = {
            'category': 'interactive',
            'test_type': 'retrieval',
            'category_type': 'spatial elimination',
            'scene_goal_id': 'C2',
            'score': {
                'classification': '1',
                'score': 1,
                'weighted_score': 1,
                'weighted_score_worth': 1,
                'confidence': 1,
                'weighted_confidence': 1
            }
        }
        history_item["score"] = mcs_history_ingest.process_score(
            history_item, test_scene, True, False, None, False, None, None)
        self.assertEqual(history_item['score']['score'], 1)
        self.assertEqual(history_item['score']['weighted_score'], 1)
        self.assertEqual(history_item['score']['weighted_score_worth'], 1)
        self.assertEqual(history_item['score']['weighted_confidence'], 1)


    def test_other_weighted_cube_scoring(self):
        test_scene = {
            "goal": {
                "sceneInfo": {
                    "tertiaryType": "shape constancy"
                },
                'answer': {
                    'choice': 'plausible'
                }
            }
        }

        history_item = {
            'category': 'passive',
            'category_type': 'shape constancy',
            'test_type': 'intuitive physics',
            'scene_goal_id': 'A1',
            'score': {
                'classification': '1',
                'score': 1,
                'weighted_score': 1,
                'weighted_score_worth': 1,
                'confidence': 1,
                'weighted_confidence': 1
            }
        }
        history_item["score"] = mcs_history_ingest.process_score(
            history_item, test_scene, True, False, None, False, None, None)
        self.assertEqual(history_item['score']['score'], 1)
        self.assertEqual(history_item['score']['weighted_score'], 2)
        self.assertEqual(history_item['score']['weighted_score_worth'], 2)
        self.assertEqual(history_item['score']['weighted_confidence'], 2)

        history_item = {
            'category': 'passive',
            'category_type': 'shape constancy',
            'test_type': 'intuitive physics',
            'scene_goal_id': 'A2',
            'score': {
                'classification': '1',
                'score': 1,
                'weighted_score': 1,
                'weighted_score_worth': 1,
                'confidence': 1,
                'weighted_confidence': 1
            }
        }
        history_item["score"] = mcs_history_ingest.process_score(
            history_item, test_scene, True, False, None, False, None, None)
        self.assertEqual(history_item['score']['score'], 1)
        self.assertEqual(history_item['score']['weighted_score'], 8)
        self.assertEqual(history_item['score']['weighted_score_worth'], 8)
        self.assertEqual(history_item['score']['weighted_confidence'], 8)

        test_scene = {
            "goal": {
                "sceneInfo": {
                    "tertiaryType": "support relations"
                }
            }
        }

        history_item = {
            'category': 'interactive',
            'test_type': 'retrieval',
            'category_type': 'support relations',
            'scene_goal_id': 'A1',
            'score': {
                'classification': '1',
                'score': 1,
                'weighted_score': 0,
                'weighted_score_worth': 0,
                'confidence': 1,
                'weighted_confidence': 0
            }
        }
        history_item["score"] = mcs_history_ingest.process_score(
            history_item, test_scene, 1, 1, None, False, None, None)
        self.assertEqual(history_item['score']['score'], 1)
        self.assertEqual(history_item['score']['weighted_score'], 1)
        self.assertEqual(history_item['score']['weighted_score_worth'], 1)
        self.assertEqual(history_item['score']['weighted_confidence'], 1)


    def test_weighted_cube_scoring_confidence_none(self):
        test_scene = {
            "goal": {
                "sceneInfo": {
                    "tertiaryType": "shape constancy"
                },
                'answer': {
                    'choice': 'plausible'
                }
            }
        }

        history_item = {
            'category': 'passive',
            'category_type': 'shape constancy',
            'test_type': 'intuitive physics',
            'scene_goal_id': 'A1',
            'score': {
                'classification': '1',
                'score': 1,
                'weighted_score': 1,
                'weighted_score_worth': 1,
                'confidence': "None",
                'weighted_confidence': 1
            }
        }
        history_item["score"] = mcs_history_ingest.process_score(
            history_item, test_scene, True, False, None, False, None, None)
        self.assertEqual(history_item['score']['score'], 1)
        self.assertEqual(history_item['score']['weighted_score'], 2)
        self.assertEqual(history_item['score']['weighted_score_worth'], 2)
        self.assertIsNone(history_item['score']['weighted_confidence'])

        history_item = {
            'category': 'passive',
            'category_type': 'shape constancy',
            'test_type': 'intuitive physics',
            'scene_goal_id': 'A2',
            'score': {
                'classification': '1',
                'score': 1,
                'weighted_score': 1,
                'weighted_score_worth': 1,
                'confidence': "None",
                'weighted_confidence': 1
            }
        }
        history_item["score"] = mcs_history_ingest.process_score(
            history_item, test_scene, True, False, None, False, None, None)
        self.assertEqual(history_item['score']['score'], 1)
        self.assertEqual(history_item['score']['weighted_score'], 8)
        self.assertEqual(history_item['score']['weighted_score_worth'], 8)
        self.assertIsNone(history_item['score']['weighted_confidence'])

        test_scene = {
            "goal": {
                "sceneInfo": {
                    "tertiaryType": "support relations"
                }
            }
        }

        history_item = {
            'category': 'interactive',
            'test_type': 'retrieval',
            'category_type': 'support relations',
            'scene_goal_id': 'A1',
            'score': {
                'classification': '1',
                'score': 1,
                'weighted_score': 0,
                'weighted_score_worth': 0,
                'confidence': "None",
                'weighted_confidence': 0
            }
        }
        history_item["score"] = mcs_history_ingest.process_score(
            history_item, test_scene, 1, 1, None, False, None, None)
        self.assertEqual(history_item['score']['score'], 1)
        self.assertEqual(history_item['score']['weighted_score'], 1)
        self.assertEqual(history_item['score']['weighted_score_worth'], 1)
        self.assertIsNone(history_item['score']['weighted_confidence'])


    def test_build_new_step_obj_interactive(self):
        step = {
            "step": 1,
            "action": "MoveAhead",
            "args": {},
            "classification": None,
            "confidence": None,
            "violations_xy_list": None,
            "internal_state": None,
            "output": {
                "goal": {
                    "metadata": {
                        "target": {
                            "id": "9d31fa87-193f-4c08-bf6c-9eff9b30e341",
                            "position": {
                                "x": -3.654195547103882,
                                "y": 3.2224996089935303,
                                "z": 3.75
                            }
                        },
                        "category": "retrieval"
                    }
                },
                "physics_frames_per_second": 20,
                "return_status": "SUCCESSFUL",
                "reward": -0.001
            },
            "delta_time_millis": 12464.299655999997,
            "target_visible": True
        }

        corner_visit_order = []
        interactive_goal_achieved = 0
        interactive_reward = 0

        (
            new_step,
            interactive_reward,
            interactive_goal_achieved,
            corner_visit_order
        ) = mcs_history_ingest.build_new_step_obj(
            step,
            interactive_reward,
            interactive_goal_achieved,
            1,
            [],
            [],
            [],
            False)

        self.assertIsNotNone(new_step)
        self.assertEqual(new_step["stepNumber"], 1)
        self.assertEqual(new_step["action"], "MoveAhead")
        self.assertEqual(new_step["args"], {})
        self.assertIsNone(new_step["classification"])
        self.assertIsNone(new_step["confidence"])
        self.assertIsNone(new_step["internal_state"])
        self.assertEqual(new_step["delta_time_millis"], step["delta_time_millis"])
        self.assertIsNone(new_step["violations_xy_list"], step["violations_xy_list"])
        self.assertEqual(new_step["output"]["physics_frames_per_second"], step["output"]["physics_frames_per_second"])
        self.assertEqual(new_step["output"]["return_status"], step["output"]["return_status"])
        self.assertEqual(new_step["output"]["reward"], step["output"]["reward"])
        self.assertEqual(new_step["target_visible"], step["target_visible"])
        self.assertEqual(new_step["output"]["target"], step["output"]["goal"]["metadata"]["target"])


if __name__ == '__main__':
    unittest.main()
