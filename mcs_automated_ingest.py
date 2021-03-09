import boto3
import json
import os
import mcs_scene_ingest

# Create SQS client
sqs = boto3.resource('sqs')
queue = sqs.get_queue_by_name(QueueName='mongo-mcs-ingestion-queue')
s3 = boto3.resource('s3')

def process_message(message):
    receipt_handle = message.message_id
    message_body = json.loads(message.body)

    for record in message_body["Records"]:
        # Download File
        bucket = s3.Bucket(record["s3"]["bucket"]["name"])
        history_file = record["s3"]["object"]["key"]
        basename = os.path.basename(history_file)
        print(f"Downloading {basename}")
        bucket.download_file(history_file, basename)

        # Ingest File
        mcs_scene_ingest.automated_history_ingest_file(basename, "")

        # Delete File
        print(f"Deleting {basename}")
        os.remove(basename)

def main():
    while True:
        all_messages = queue.receive_messages()
        for message in all_messages:
            process_message(message)
            message.delete()


if __name__ == '__main__':
    main()