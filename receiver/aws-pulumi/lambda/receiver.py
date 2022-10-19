#!/usr/bin/env python
import os
import hmac
import hashlib
import json
import logging
import traceback
import boto3
import botocore.exceptions
from botocore.exceptions import ClientError
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

GITHUB_SECRET = os.environ["GITHUB_SECRET"]
SQS_QUEUE = os.environ['SQS_QUEUE']
SQS_REGION = os.environ['SQS_REGION']


def return_http_code(code, item):
    return {
        'statusCode': code,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(item)
    }


def exception_handler(e):
    return return_http_code(500,  {'message': str(e)})


def handler(event, context):
    try:
        # Validate if the request is a POST
        if event['httpMethod'] != 'POST':
            return return_http_code(405, {'message': 'Method Not Allowed'})

        # Check if path is correct
        if (event['path'] != '/github-webhook' and event['path'] != '/github-webhook/'):
            return return_http_code(400, {'message': 'Event not found: ' + event['path']})
            
        # Validate if the request has a body
        if 'body' not in event:
            return return_http_code(400, {'message': 'Bad Request'})

        # Populate the data that was sent so the hmac check is ok.
        # request.get_data()

        # Extract signature header
        signature = event['headers']['X-Hub-Signature']

        #signature = request.headers.get("X-Hub-Signature")
        if not signature or not signature.startswith("sha1="):
            return_http_code(400, "X-Hub-Signature required")

        # Get payload
        payload = json.loads(event['body'])
        print("Payload: " + str(payload))        

        # Create local hash of payload
        digest = hmac.new(
            GITHUB_SECRET.encode(),
            event['body'].encode('utf-8'),
            hashlib.sha1
        ).hexdigest()

        if not hmac.compare_digest(signature, "sha1=" + digest):
            return_http_code(400,  "Invalid signature")

        # Create a big dictionary with headers and payload.
        message = {
            'headers': dict(event['headers']),
            'payload': payload
        }

        # Send the message to Amazon SQS.
        sqs = boto3.resource('sqs', region_name=SQS_REGION)
        print("QueueName=" + SQS_QUEUE)
        queue = sqs.get_queue_by_name(QueueName=SQS_QUEUE)
        response = queue.send_message(
            MessageBody=json.dumps(message)
        )

        return return_http_code(200, f"OK (ID: {response.get('MessageId')})")

    except Exception as e:
        logger.error(str(e))
        traceback.print_exc()
        return exception_handler(e)
