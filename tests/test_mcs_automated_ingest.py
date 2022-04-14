import unittest
import boto3
import os

from moto import mock_s3, mock_sqs
from unittest.mock import patch

import mcs_automated_ingest as mai

class TestMcsAutomatedIngest(unittest.TestCase):

    test_bucket = "test-mcs"
    test_file = "filename.json"

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    @mock_s3
    def test_download_file(self):
        # create bucket and put an empty file in it
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket=self.test_bucket)
        s3.put_object(
            Bucket=self.test_bucket,
            Key=self.test_file,
            Body=''
        )

        record = {
            "s3": {
                "bucket": {"name": self.test_bucket},
                "object": {"key": self.test_file}
                }
            }

        # override the s3 resource that points to "live" (test smell)
        mai.s3 = boto3.resource("s3")
        basename = mai.download_file(record)
        self.assertTrue(os.path.exists(basename))

    @mock_s3
    def test_download_file_with_path(self):
        # create bucket and put an empty file in it
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket=self.test_bucket)
        s3.put_object(
            Bucket=self.test_bucket,
            Key=f'path/to/{self.test_file}',
            Body=''
        )

        record = {
            "s3": {
                "bucket": {"name": self.test_bucket},
                "object": {"key": f"path/to/{self.test_file}"}
                }
            }

        # override the s3 resource that points to "live" (test smell)
        mai.s3 = boto3.resource("s3")
        basename = mai.download_file(record)
        self.assertTrue(os.path.exists(basename))

    def test_ingest_scene_file(self):
        '''Ensure scene ingest is called with SCENE_MESSAGE'''
        with patch("mcs_scene_ingest.automated_scene_ingest_file") as patched_function:
            mai.ingest_file("basename", mai.SCENE_MESSAGE, 'mcs', client=None)
        patched_function.assert_called()
        
    def test_ingest_history_file(self):
        '''Ensure history ingest is called with HISTORY_MESSAGE'''
        with patch("mcs_history_ingest.automated_history_ingest_file") as patched_function:
            mai.ingest_file("basename", mai.HISTORY_MESSAGE, 'mcs', client=None)
        patched_function.assert_called()

    @mock_sqs
    def test_ingest_scene_file_with_error(self):
        '''While ingesting a scene file, an exception occurs'''
        sqs = boto3.resource('sqs', region_name='us-east-1')
        mai.error_queue = sqs.create_queue(QueueName='ingest-error')
        sqs_client = boto3.client('sqs', region_name='us-east-1')

        with patch("mcs_scene_ingest.automated_scene_ingest_file") as patched_function:
            patched_function.side_effect = Exception()
            mai.ingest_file("basename", mai.SCENE_MESSAGE, "mcs", client=None)

        response = sqs_client.get_queue_attributes(
            QueueUrl=mai.error_queue.url,
            AttributeNames=['ApproximateNumberOfMessages']

        )
        self.assertEqual(int(response['Attributes']['ApproximateNumberOfMessages']), 1)

    @mock_sqs
    def test_ingest_history_file_with_error(self):
        '''While ingesting a history file, an exception occurs'''
        sqs = boto3.resource('sqs', region_name='us-east-1')
        mai.error_queue = sqs.create_queue(QueueName='ingest-error')
        sqs_client = boto3.client('sqs', region_name='us-east-1')

        with patch("mcs_history_ingest.automated_history_ingest_file") as patched_function:
            patched_function.side_effect = Exception()
            mai.ingest_file("basename", mai.HISTORY_MESSAGE, "mcs", client=None)

        response = sqs_client.get_queue_attributes(
            QueueUrl=mai.error_queue.url,
            AttributeNames=['ApproximateNumberOfMessages']

        )
        self.assertEqual(int(response['Attributes']['ApproximateNumberOfMessages']), 1)

    @mock_sqs
    def test_ingest_file_with_invalid_message_type(self):
        '''Nothing happens if the message type is not history or scene types'''
        sqs = boto3.resource('sqs', region_name='us-east-1')
        mai.error_queue = sqs.create_queue(QueueName='ingest-error')
        sqs_client = boto3.client('sqs', region_name='us-east-1')

        mai.ingest_file("basename", "invalid_msg_type", "mcs", client=None)

        response = sqs_client.get_queue_attributes(
            QueueUrl=mai.error_queue.url,
            AttributeNames=['ApproximateNumberOfMessages']

        )
        self.assertEqual(int(response['Attributes']['ApproximateNumberOfMessages']), 0)
