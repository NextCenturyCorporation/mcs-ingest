import boto3
import json
import os
import mcs_scene_ingest

# Create SQS client
sqs = boto3.resource('sqs')
history_queue = sqs.get_queue_by_name(QueueName='mongo-mcs-ingestion-queue')
scene_queue = sqs.get_queue_by_name(QueueName='mcs-scene-ingestion-queue')
s3 = boto3.resource('s3')

# Message Type Constants
HISTORY_MESSAGE = "history"
SCENE_MESSAGE = "scene"

def process_message(message, message_type):
    message_body = json.loads(message.body)
    for record in message_body["Records"]:
        # Download File
        bucket = s3.Bucket(record["s3"]["bucket"]["name"])
        history_file = record["s3"]["object"]["key"]
        basename = os.path.basename(history_file)
        print(f"Downloading {basename}")
        bucket.download_file(history_file, basename)

        # Ingest File
        if message_type == HISTORY_MESSAGE:
            mcs_scene_ingest.automated_history_ingest_file(basename, "")
        if message_type == SCENE_MESSAGE:
            mcs_scene_ingest.automated_scene_ingest_file(basename, "")

        # Delete File
        print(f"Deleting {basename}")
        os.remove(basename)

def main():
    while True:
        # Check for messages on history queue
        history_messages = history_queue.receive_messages()
        for message in history_messages:
            process_message(message, HISTORY_MESSAGE)
            message.delete()

        # Check for messages on scene queue
        scene_messages = scene_queue.receive_messages()
        for message in scene_messages:
            process_message(message, SCENE_MESSAGE)
            message.delete()


if __name__ == '__main__':
    main()