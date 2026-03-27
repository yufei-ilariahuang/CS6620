"""
Logging Lambda – SQS Consumer
Logs S3 event details (object name + size delta) to CloudWatch.
For deletions, queries CloudWatch logs to find original size.
"""
import os
import boto3
import json
import re
from datetime import datetime, timezone

REGION = os.environ["REGION"]
LOG_GROUP = os.environ.get("LOG_GROUP", "/aws/lambda/logging")

logs_client = boto3.client("logs", region_name=REGION)


def find_object_size_in_logs(object_name):
    """
    Query CloudWatch logs to find original size of deleted object.
    Returns size if found, otherwise 0.
    """
    try:
        # Search for creation event of this object
        response = logs_client.filter_log_events(
            logGroupName=LOG_GROUP,
            filterPattern=f'{{ $.object_name = "{object_name}" }}',
            limit=1
        )

        for event in response.get("events", []):
            try:
                log_data = json.loads(event["message"])
                if "size_delta" in log_data:
                    return abs(int(log_data["size_delta"]))
            except:
                pass

        return 0

    except Exception as e:
        print(f"[WARN] Could not query logs for {object_name}: {e}")
        return 0


def lambda_handler(event, context):
    """
    Consume SQS messages (S3 events).
    Log event in JSON format: {"object_name": "...", "size_delta": N}
    For deletes, size_delta is negative.
    """
    
    for record in event.get("Records", []):
        try:
            # SQS message body is the SNS message JSON
            body = json.loads(record["body"])
            
            # SNS wraps the actual S3 event
            message = json.loads(body.get("Message", "{}"))
            
            # Extract S3 event records
            for s3_record in message.get("Records", []):
                event_name = s3_record.get("eventName", "")
                bucket = s3_record.get("s3", {}).get("bucket", {}).get("name", "")
                key = s3_record.get("s3", {}).get("object", {}).get("key", "")
                
                # For create events, get size directly
                if event_name.startswith("ObjectCreated"):
                    size = s3_record.get("s3", {}).get("object", {}).get("size", 0)
                    size_delta = int(size)
                
                # For delete events, query logs to find original size
                elif event_name.startswith("ObjectRemoved"):
                    size = find_object_size_in_logs(key)
                    size_delta = -size
                
                else:
                    continue
                
                # Log in JSON format
                log_entry = {
                    "object_name": key,
                    "size_delta": size_delta,
                    "event": event_name,
                    "bucket": bucket,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                print(json.dumps(log_entry))
                
        except Exception as e:
            print(f"[ERROR] Failed to process message: {e}")

    return {
        "statusCode": 200,
        "body": "Logged S3 events"
    }
