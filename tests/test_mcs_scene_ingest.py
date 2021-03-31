import unittest
import mcs_scene_ingest

TEST_SCENE_FILE_NAME = "test_juliett_0001_01_debug.json"
TEST_HISTORY_FILE_NAME = "test_eval_3-5_level2_baseline_juliett_0001_01.json"


class TestMcsSceneIngest(unittest.TestCase):

    def test_load_json_file(self):
        scene_file = mcs_scene_ingest.load_json_file(
            "tests", TEST_SCENE_FILE_NAME)
        self.assertEqual(scene_file["name"], "juliett_0001_01")
        self.assertEqual(scene_file["training"], False)

    def test_delete_keys_from_scene(self):
        test_scene = {
            "name": "test",
            "version": 2,
            "image": "image_to_delete",
            "sequenceNumber": 1,
            "hypercubeNumber": 5,
            "sceneNumber": 100
        }

        scene_removed_keys = mcs_scene_ingest.delete_keys_from_scene(
            test_scene, mcs_scene_ingest.KEYS_TO_DELETE)
        self.assertEqual(scene_removed_keys["name"], "test")
        self.assertEqual(scene_removed_keys["version"], 2)
        self.assertEqual(scene_removed_keys.get("image"), None)
        self.assertEqual(scene_removed_keys.get("sequenceNumber"), None)
        self.assertEqual(scene_removed_keys.get("hypercubeNumber"), None)
        self.assertEqual(scene_removed_keys.get("sceneNumber"), None)

    def test_find_scene_files(self):
        scene_files = mcs_scene_ingest.find_scene_files("tests")
        self.assertEqual(len(scene_files), 1)
        self.assertEqual(scene_files[0], TEST_SCENE_FILE_NAME)

    def test_find_history_files(self):
        history_files = mcs_scene_ingest.find_history_files("tests", "json")
        self.assertEqual(len(history_files), 2)

    def test_build_scene_item(self):
        scene = mcs_scene_ingest.build_scene_item(
            TEST_SCENE_FILE_NAME, "tests", None)
        self.assertEqual(scene["eval"], "Evaluation 3.5 Scenes")
        self.assertEqual(scene["test_num"], 1)
        self.assertEqual(scene.get("sequenceNumber"), None)
        self.assertEqual(scene.get("hypercubeNumber"), None)

    def test_determine_evaluation_name(self):
        eval_name = mcs_scene_ingest.determine_evaluation_name(
            "Eval3", "eval3.5")
        self.assertEqual(eval_name, "Eval3")
        eval_name = mcs_scene_ingest.determine_evaluation_name(
            None, "eval3.5")
        self.assertEqual(eval_name, "eval3.5")
        eval_name = mcs_scene_ingest.determine_evaluation_name(
            None, "eval_3-5")
        self.assertEqual(eval_name, "Evaluation 3.5 Results")

    def test_determine_team_mapping_name(self):
        team_name = mcs_scene_ingest.determine_team_mapping_name("ibm")
        self.assertEqual(team_name, "ibm")
        team_name = mcs_scene_ingest.determine_team_mapping_name("mit")
        self.assertEqual(team_name, "IBM-MIT-Harvard-Stanford")


if __name__ == '__main__':
    unittest.main()
