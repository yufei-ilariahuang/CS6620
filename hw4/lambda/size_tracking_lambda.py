"""
Size-Tracking Lambda – SQS Consumer
Processes S3 events from SQS and updates DynamoDB with bucket size.
"""
import os
import boto3
import json
from datetime import datetime, timezone

BUCKET_NAME = os.environ["BUCKET_NAME"]
TABLE_NAME  = os.environ["TABLE_NAME"]
REGION      = os.environ["REGION"]

s3  = boto3.client("s3",  region_name=REGION)
ddb = boto3.resource("dynamodb", region_name=REGION)


def compute_bucket_size():
    """Get total size and object count in bucket."""
    total_size = 0
    n_objects  = 0

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get("Contents", []):
            total_size += obj["Size"]
            n_objects  += 1

    return total_size, n_objects


def lambda_handler(event, context):
    """
    Consume SQS messages (S3 events wrapped by SNS).
    Each message contains S3 event details.
    Update DynamoDB with current bucket state.
    """
    
    for record in event.get("Records", []):
        try:
            # SQS message body is the SNS message JSON
            body = json.loads(record["body"])
            
            # SNS wraps the actual S3 event
            message = json.loads(body.get("Message", "{}"))
            
            print(f"[SQS] Received S3 event: {message.get('eventName', 'unknown')}")
            
        except Exception as e:
            print(f"[ERROR] Failed to parse message: {e}")
            continue

    # Compute and record current bucket state
    total_size, n_objects = compute_bucket_size()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")

    table = ddb.Table(TABLE_NAME)
    table.put_item(Item={
        "bucketName": BUCKET_NAME,
        "timeStamp":  timestamp,
        "totalSize":  total_size,
        "nObject":    n_objects,
    })

    print(f"[OK] bucketName={BUCKET_NAME}, totalSize={total_size}, nObject={n_objects}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "totalSize": total_size,
            "nObject": n_objects
        })
    }
