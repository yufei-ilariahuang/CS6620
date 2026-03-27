import json
import os
import time

import boto3
from boto3.dynamodb.conditions import Key

DEST_BUCKET = os.environ["DEST_BUCKET"]
TABLE_NAME = os.environ["TABLE_NAME"]
STATUS_INDEX_NAME = os.environ["STATUS_INDEX_NAME"]
DISOWNED_AGE_SECONDS = int(os.environ.get("DISOWNED_AGE_SECONDS", "10"))

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def _query_expired_disowned(cutoff: int):
    """Return disowned copies older than the cutoff using the status GSI."""
    items = []
    resp = table.query(
        IndexName=STATUS_INDEX_NAME,
        KeyConditionExpression=Key("copy_status").eq("DISOWNED")
        & Key("disowned_at").lte(cutoff),
    )
    items.extend(resp.get("Items", []))

    while "LastEvaluatedKey" in resp:
        resp = table.query(
            IndexName=STATUS_INDEX_NAME,
            KeyConditionExpression=Key("copy_status").eq("DISOWNED")
            & Key("disowned_at").lte(cutoff),
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp.get("Items", []))

    return items


def lambda_handler(event, context):
    """Delete expired disowned S3 copies and remove their table rows."""
    cutoff = int(time.time()) - DISOWNED_AGE_SECONDS
    items = _query_expired_disowned(cutoff)

    deleted = 0
    for item in items:
        copy_key = item["copy_key"]
        source_key = item["source_key"]
        copy_sort = item["copy_sort"]

        try:
            s3.delete_object(Bucket=DEST_BUCKET, Key=copy_key)
        except Exception as ex:
            print(f"Failed to delete disowned copy from S3 {copy_key}: {ex}")
            continue

        table.delete_item(
            Key={
                "source_key": source_key,
                "copy_sort": copy_sort,
            }
        )
        deleted += 1

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "deleted_count": deleted,
                "cutoff_epoch": cutoff,
            }
        ),
    }
