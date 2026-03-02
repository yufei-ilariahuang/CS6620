import os
import boto3
from datetime import datetime, timezone

BUCKET_NAME = os.environ["BUCKET_NAME"]
TABLE_NAME  = os.environ["TABLE_NAME"]
REGION      = os.environ["REGION"]

s3  = boto3.client("s3",  region_name=REGION)
ddb = boto3.resource("dynamodb", region_name=REGION)


def lambda_handler(event, context):
    # ── compute total size and object count ───────────────────────────────────
    total_size = 0
    n_objects  = 0

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get("Contents", []):
            total_size += obj["Size"]
            n_objects  += 1

    # ── write record to DynamoDB ──────────────────────────────────────────────
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")

    table = ddb.Table(TABLE_NAME)
    table.put_item(Item={
        "bucketName": BUCKET_NAME,
        "timeStamp":  timestamp,
        "totalSize":  total_size,
        "nObject":    n_objects,
    })

    print(f"[OK] bucketName={BUCKET_NAME}, totalSize={total_size}, "
          f"nObject={n_objects}, timeStamp={timestamp}")

    return {
        "statusCode": 200,
        "body": f"Recorded: totalSize={total_size}, nObject={n_objects}"
    }