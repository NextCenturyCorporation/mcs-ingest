import unittest
import boto3
import os

from moto import mock_s3

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
