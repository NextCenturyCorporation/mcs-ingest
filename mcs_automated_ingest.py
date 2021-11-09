import json
import logging
import os
import boto3
import traceback

import mcs_scene_ingest

# Create SQS client
sqs = boto3.resource('sqs')
history_queue = sqs.get_queue_by_name(QueueName='mongo-mcs-ingestion-queue')
scene_queue = sqs.get_queue_by_name(QueueName='mcs-scene-ingestion-queue')
error_queue = sqs.get_queue_by_name(QueueName='ingest-error')
dev_history_queue = sqs.get_queue_by_name(
    QueueName='dev-mongo-mcs-ingestion-queue')
dev_scene_queue = sqs.get_queue_by_name(
    QueueName='dev-mcs-scene-ingestion-queue')
dev_error_queue = sqs.get_queue_by_name(
    QueueName='dev-ingest-error')
s3 = boto3.resource('s3')

# Message Type Constants
HISTORY_MESSAGE = "history"
SCENE_MESSAGE = "scene"


def process_message(message, message_type, db_string):
    message_body = json.loads(message.body)
    for record in message_body["Records"]:
        # Download File
        bucket = s3.Bucket(record["s3"]["bucket"]["name"])
        history_file = record["s3"]["object"]["key"]
        basename = os.path.basename(history_file)
        logging.info(f"Downloading {basename}")
        bucket.download_file(history_file, basename)

        # Ingest File
        try:
            if message_type == HISTORY_MESSAGE:
                mcs_scene_ingest.automated_history_ingest_file(
                    basename, "", db_string)
            if message_type == SCENE_MESSAGE:
                mcs_scene_ingest.automated_scene_ingest_file(
                    basename, "", db_string)
        except Exception as e:
            logging.info(f"Error {traceback.format_exc()}")
            eq =  error_queue if db_string == "mcs" else dev_error_queue
            response = eq.send_message(MessageBody='IngestError', MessageAttributes={
                'file': {'StringValue': str(basename), 'DataType': 'String'},
                'error': {'StringValue': str(traceback.format_exc()), 'DataType': 'String'}
            })
            logging.info(f"Sending {response}")

        # Delete File
        logging.info(f"Deleting {basename}")
        os.remove(basename)


def main():
    while True:
        # Check for messages on history queue
        history_messages = history_queue.receive_messages()
        for message in history_messages:
            process_message(message, HISTORY_MESSAGE, "mcs")
            message.delete()

        # Check for messages on scene queue
        scene_messages = scene_queue.receive_messages()
        for message in scene_messages:
            process_message(message, SCENE_MESSAGE, "mcs")
            message.delete()

        # Check for messages on dev history queue
        dev_history_messages = dev_history_queue.receive_messages()
        for message in dev_history_messages:
            process_message(message, HISTORY_MESSAGE, "dev")
            message.delete()

        # Check for messages on dev scene queue
        dev_scene_messages = dev_scene_queue.receive_messages()
        for message in dev_scene_messages:
            process_message(message, SCENE_MESSAGE, "dev")
            message.delete()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()
