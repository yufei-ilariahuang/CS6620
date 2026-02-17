import boto3
import time
import urllib.request

BUCKET_NAME  = "testbucket-lia-hw2"
REGION       = "us-west-1"
PLOTTING_URL = "https://YOUR_FUNCTION_URL_HERE"  # replace with plotting lambda Function URL

s3 = boto3.client("s3", region_name=REGION)


def put_object(key, content):
    s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=content.encode("utf-8"))
    print(f"[PUT] {key} ({len(content.encode('utf-8'))} bytes)")


def delete_object(key):
    s3.delete_object(Bucket=BUCKET_NAME, Key=key)
    print(f"[DELETE] {key}")


def lambda_handler(event, context):
    # 1. Create assignment1.txt — 19 bytes
    put_object("assignment1.txt", "Empty Assignment 1")
    time.sleep(2)

    # 2. Update assignment1.txt — 28 bytes
    put_object("assignment1.txt", "Empty Assignment 2222222222")
    time.sleep(2)

    # 3. Delete assignment1.txt — 0 bytes
    delete_object("assignment1.txt")
    time.sleep(2)

    # 4. Create assignment2.txt — 2 bytes
    put_object("assignment2.txt", "33")
    time.sleep(2)
    
    # 5. Update assignment1.txt — 28 bytes
    put_object("assignment1.txt", "Empty Assignment 2222222222")
    time.sleep(2)
    
    # 6. Delete assignment2.txt — 0 bytes
    delete_object("assignment2.txt")
    time.sleep(2)

    # 7. Call plotting lambda via REST API
    print(f"[PLOT] Calling plotting lambda at {PLOTTING_URL}")
    req = urllib.request.Request(PLOTTING_URL, method="GET")
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8")
        print(f"[PLOT] Response: {body}")

    return {
        "statusCode": 200,
        "body": "Driver complete. Check DynamoDB and S3 for plot."
    }