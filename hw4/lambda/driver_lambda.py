"""
Driver Lambda – Orchestrator
Runs the hw4 sequence with SNS/SQS/Alarm integration.
"""
import os
import boto3
import time
import urllib.request
import json

BUCKET_NAME  = os.environ["BUCKET_NAME"]
REGION       = os.environ["REGION"]
PLOTTING_URL = os.environ["PLOTTING_URL"]

s3 = boto3.client("s3", region_name=REGION)


def put_object(key, content):
    """Create or update S3 object."""
    s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=content.encode("utf-8"))
    size = len(content.encode("utf-8"))
    print(f"[PUT] {key} ({size} bytes)")


def lambda_handler(event, context):
    """
    Sequence:
    1. Create assignment1.txt (19 bytes) → total=19, no alarm
    2. Create assignment2.txt (28 bytes) → total=47, alarm fires → delete assignment2.txt
    3. Create assignment3.txt (2 bytes) → total=21, alarm fires → delete assignment1.txt
    4. Call plotting lambda
    """
    
    # 1. Create assignment1.txt (19 bytes)
    put_object("assignment1.txt", "Empty Assignment 1")
    time.sleep(3)

    # 2. Create assignment2.txt (28 bytes) → trigger first alarm
    put_object("assignment2.txt", "Empty Assignment 2222222222")
    print("[WAIT] Waiting for alarm to trigger cleaner (delete assignment2.txt)...")
    time.sleep(5)

    # 3. Create assignment3.txt (2 bytes) → trigger second alarm
    put_object("assignment3.txt", "33")
    print("[WAIT] Waiting for alarm to trigger cleaner (delete assignment1.txt)...")
    time.sleep(5)

    # 4. Call plotting lambda via REST API
    print(f"[PLOT] Calling plotting lambda at {PLOTTING_URL}")
    try:
        req = urllib.request.Request(PLOTTING_URL, method="GET")
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            print(f"[PLOT] Response: {body}")
    except Exception as e:
        print(f"[ERROR] Plotting call failed: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Driver complete",
            "bucket": BUCKET_NAME,
            "plot_url": PLOTTING_URL
        })
    }
