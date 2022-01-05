import unittest
import time
import docker

from pymongo import MongoClient

class MongoDockerTest(unittest.TestCase):

    mongo_client = None
    mongo_host_port = 27027

    @classmethod
    def create_mongo_container(cls, docker_client, api_client, timeout=60):
        '''Helper method to create the mongodb container'''
        mongo_container = docker_client.containers.run(
            'mongo:latest',
            ports={27017:cls.mongo_host_port},
            healthcheck= {
                "Test": f"mongo --eval \'db.runCommand(\"ping\").ok\' " \
                        f"localhost:{cls.mongo_host_port}/test --quiet",
                "Interval": 1_000_000 * 1_000
            },
            remove=True,
            detach=True
        )
        health = None
        max_time = time.time() + timeout
        while health != "healthy" and (time.time() < max_time):
            inspection = api_client.inspect_container(mongo_container.id)
            health = inspection["State"]["Health"]["Status"]
            time.sleep(1)
        return mongo_container

    @classmethod
    def setUpClass(cls):
        # connect to docker daemon
        cls.docker_client = docker.from_env()
        # create low-level API client
        cls.api_client = docker.APIClient(
            base_url="unix://var/run/docker.sock")
        cls.mongo_container = cls.create_mongo_container(
            cls.docker_client,
            cls.api_client)
        cls.mongo_client = MongoClient(host="localhost", port=cls.mongo_host_port)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.mongo_container.stop()
        cls.docker_client.close()
        cls.api_client.close()

    def setUp(self):
        db = self.mongo_client['test']
        collection = db['coll']
        collection.insert_one({'name': 'bob'})

    def test_creation(self):
        db = self.mongo_client['test']
        collection = db['coll']
        record = collection.find_one()
        self.assertIn('name', record)
        self.assertEqual(record['name'], 'bob')
