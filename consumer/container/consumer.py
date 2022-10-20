#!/usr/bin/env python
import datetime
import json
import os
import time
from turtle import end_fill

import boto3
import requests

JENKINS_URL = os.environ['JENKINS_URL']
SQS_QUEUE_URL = os.environ['SQS_QUEUE_URL']
SQS_REGION = os.environ['SQS_REGION']

sqs = boto3.client('sqs', region_name=SQS_REGION)

print("Webhook consumer starting up!")

while True:
    message_list = sqs.receive_message(
        QueueUrl=SQS_QUEUE_URL,
        WaitTimeSeconds=20,
        MaxNumberOfMessages=10
    )
    if not message_list or "Messages" not in message_list:
        time.sleep(5)
        continue

    for message in message_list["Messages"]:
        print(
            f"Got message: {message['MessageId']} at {datetime.datetime.now().isoformat()}")
        parsed = json.loads(message["Body"])
        original_headers = parsed['headers']
        payload = parsed['payload']

        print("Sending to Jenkins...")
        try:
            # Set up our headers.
            headers = {}
            headers['Content-Type'] = "application/json"
            # Ignore message if X-GitHub-Event is not present
            if 'X-GitHub-Event' in original_headers:
                headers['X-Github-Event'] = original_headers['X-Github-Event']

                # Post the message to jenkins.
                resp = requests.post(
                    JENKINS_URL,
                    headers=headers,
                    data=json.dumps(payload),
                    verify=False
                )
                print(resp.text)
            else:
                print("--")
                print("No X-GitHub-Event header found, ignoring message.")
                print(original_headers)
                print(payload)
                print("--")
            

            # Delete the message if we made it this far.
            sqs.delete_message(
                QueueUrl=SQS_QUEUE_URL,
                ReceiptHandle=message['ReceiptHandle']
            )
        except Exception as e:
            print(f"Error: {e}")

    time.sleep(5)
