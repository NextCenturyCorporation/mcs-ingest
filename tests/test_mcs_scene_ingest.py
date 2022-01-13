import docker
import logging
import time
import unittest
import warnings

import mcs_scene_ingest
import create_collection_keys

from pymongo import MongoClient

TEST_SCENE_FILE_NAME = "test_juliett_0001_01_debug.json"
# TEST_INTERACTIVE_SCENE_FILE_NAME = "occluders_0001_17_I1_debug.json"
TEST_FOLDER = "tests"

class TestMcsSceneIngestMongo(unittest.TestCase):
    '''Test database functionality of mcs_scene_ingest using docker/mongo'''

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

    def tearDown(self):
        '''Drop the database and close the connection'''
        self.mongo_client.drop_database('mcs')
        self.mongo_client.close()

    def test_automated_scene_ingest_file(self):
        scene = self.mongo_client['mcs'][mcs_scene_ingest.SCENE_INDEX].find_one()
        self.assertTrue(scene['name'] in TEST_SCENE_FILE_NAME)

    def test_automated_scene_ingest_file_already_exists(self):
        scene = self.mongo_client['mcs'][mcs_scene_ingest.SCENE_INDEX].find_one()
        self.assertTrue(scene['name'] in TEST_SCENE_FILE_NAME)

        # process the same scene file a second time
        # which ingest should ignore
        mcs_scene_ingest.automated_scene_ingest_file(
            file_name=TEST_SCENE_FILE_NAME,
            folder=TEST_FOLDER,
            db_string="mcs",
            client=self.mongo_client)
        count = self.mongo_client['mcs'][mcs_scene_ingest.SCENE_INDEX].count_documents(
            {
                "name": scene["name"],
                "eval": scene["eval"]
            }
        )
        self.assertEqual(count, 1)

    def test_automated_scene_ingest_collection_key_created(self):
        scene = self.mongo_client['mcs'][mcs_scene_ingest.SCENE_INDEX].find_one()
        coll_keys = create_collection_keys.check_collection_has_key(
            scene["eval"], self.mongo_client['mcs'])
        self.assertEqual(coll_keys["name"], scene["eval"])


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


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    unittest.main()
