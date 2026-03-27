"""
Cleaner Lambda – Alarm Trigger
Deletes the largest object from the bucket when alarm fires.
"""
import os
import boto3
import json

BUCKET_NAME = os.environ["BUCKET_NAME"]
REGION      = os.environ["REGION"]

s3 = boto3.client("s3", region_name=REGION)


def lambda_handler(event, context):
    """
    Triggered by CloudWatch Alarm when SUM(TotalObjectSize) > 20.
    Finds and deletes the largest object in the bucket.
    """
    
    print(f"[CLEANER] Alarm triggered. Finding largest object in {BUCKET_NAME}...")
    
    # List all objects
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)
    objects = response.get("Contents", [])
    
    if not objects:
        print("[CLEANER] No objects in bucket.")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No objects to delete"})
        }
    
    # Find largest object
    largest = max(objects, key=lambda x: x["Size"])
    largest_key = largest["Key"]
    largest_size = largest["Size"]
    
    # Delete it
    s3.delete_object(Bucket=BUCKET_NAME, Key=largest_key)
    
    print(f"[CLEANER] Deleted: {largest_key} ({largest_size} bytes)")
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "deleted": largest_key,
            "size": largest_size
        })
    }
