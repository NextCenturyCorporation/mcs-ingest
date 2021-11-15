import boto3
import datetime
import glob
import json
import logging
import os
import random
import traceback
import urllib3
import uuid

# Get SQS Queues
sqs = boto3.resource('sqs')
media_queue = sqs.get_queue_by_name(QueueName='media-convert-queue')
dev_media_queue = sqs.get_queue_by_name(QueueName='dev-media-convert-queue')
media_error_queue = sqs.get_queue_by_name(QueueName='error-media-convert-queue')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
prod_media_endpoint = "https://vasjpylpa.mediaconvert.us-east-1.amazonaws.com"
dev_media_endpoint = "https://mqm13wgra.mediaconvert.us-east-2.amazonaws.com"

def process_message(message, message_type):
    message_body = json.loads(message.body)
    for record in message_body["Records"]:
        # Create Variables Needed for Media Convert
        assetID = str(uuid.uuid4())
        sourceS3Bucket = record['s3']['bucket']['name']
        sourceS3Key = record['s3']['object']['key']
        sourceS3 = 's3://'+ sourceS3Bucket + '/' + sourceS3Key
        sourceS3Basename = os.path.splitext(os.path.basename(sourceS3))[0]
        sourceS3Foldername = os.path.dirname(sourceS3Key)

        # Get The Evaluation number to place the converted file in
        folder_parts = sourceS3Foldername.split("-")
        destinationFoldername = "eval-resources-" + folder_parts[len(folder_parts)-1]
        
        destinationS3 = 's3://' + sourceS3Bucket + '/' + destinationFoldername + "/"
        destinationS3basename = os.path.splitext(os.path.basename(destinationS3))[0]
        mediaConvertRole = 'arn:aws:iam::795237661910:role/MediaConvertRole'

        region = 'us-east-1' if message_type == 'prod' else 'us-east-2'
        media_url = prod_media_endpoint if message_type == 'prod' else dev_media_endpoint
        body = {}
        
        # Use MediaConvert SDK UserMetadata to tag jobs with the assetID
        # Events from MediaConvert will have the assetID in UserMedata
        jobMetadata = {'assetID': assetID}

        try:
            with open('media_convert/job.json') as json_data:
                jobSettings = json.load(json_data)

            # Update the job settings with the source video from the S3 event and destination
            # paths for converted videos
            jobSettings['Inputs'][0]['FileInput'] = sourceS3
            jobSettings['OutputGroups'][0]['OutputGroupSettings'][
                'FileGroupSettings']['Destination'] = destinationS3 + sourceS3Basename
            
            # add the account-specific endpoint to the client session
            client = boto3.client('mediaconvert', region_name=region, endpoint_url=media_url, verify=False)

            # Convert the video using AWS Elemental MediaConvert
            job = client.create_job(Role=mediaConvertRole, UserMetadata=jobMetadata, Settings=jobSettings)
            
            logging.info(f"Sending {sourceS3} to MediaConvert.")
        except Exception as e:
            response = media_error_queue.send_message(MessageBody='MediaConvertError', MessageAttributes={
                'file': {'StringValue': str(sourceS3), 'DataType': 'String'},
                'error': {'StringValue': str(traceback.format_exc()), 'DataType': 'String'}
            })
            logging.info(f"Sending {response}")


def main():
    while True:
        # Check for messages on media queue
        media_messages = media_queue.receive_messages()
        for message in media_messages:
            process_message(message, "prod")
            message.delete()

        # Check for messages on dev media queue
        dev_media_messages = dev_media_queue.receive_messages()
        for message in dev_media_messages:
            process_message(message, "dev")
            message.delete()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()
