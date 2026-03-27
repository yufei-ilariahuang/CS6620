import json
import os
import time
import urllib.parse
import uuid

import boto3
from boto3.dynamodb.conditions import Attr, Key

SOURCE_BUCKET = os.environ["SOURCE_BUCKET"]
DEST_BUCKET = os.environ["DEST_BUCKET"]
TABLE_NAME = os.environ["TABLE_NAME"]

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def _decode_key(raw_key: str) -> str:
    """Decode URL-encoded S3 keys from event payloads."""
    return urllib.parse.unquote_plus(raw_key)


def _make_copy_key(source_key: str, created_at: int) -> str:
    suffix = uuid.uuid4().hex[:8]
    return f"{source_key}.copy.{created_at}.{suffix}"


def _make_copy_sort(created_at: int) -> str:
    suffix = uuid.uuid4().hex[:8]
    return f"{created_at:010d}#{suffix}"


def _handle_put(source_key: str) -> None:
    """Create a new copy and enforce max 3 owned copies per source key."""
    now = int(time.time())
    copy_key = _make_copy_key(source_key, now)
    copy_sort = _make_copy_sort(now)

    s3.copy_object(
        Bucket=DEST_BUCKET,
        Key=copy_key,
        CopySource={"Bucket": SOURCE_BUCKET, "Key": source_key},
    )

    table.put_item(
        Item={
            "source_key": source_key,
            "copy_sort": copy_sort,
            "copy_key": copy_key,
            "created_at": now,
            "copy_status": "OWNED",
            "disowned_at": 0,
        }
    )

    resp = table.query(
        KeyConditionExpression=Key("source_key").eq(source_key),
        FilterExpression=Attr("copy_status").eq("OWNED"),
        ScanIndexForward=True,
    )
    owned_items = resp.get("Items", [])

    while "LastEvaluatedKey" in resp:
        resp = table.query(
            KeyConditionExpression=Key("source_key").eq(source_key),
            FilterExpression=Attr("copy_status").eq("OWNED"),
            ScanIndexForward=True,
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        owned_items.extend(resp.get("Items", []))

    if len(owned_items) <= 3:
        return

    extra_count = len(owned_items) - 3
    to_delete = owned_items[:extra_count]

    for item in to_delete:
        old_copy_key = item["copy_key"]
        try:
            s3.delete_object(Bucket=DEST_BUCKET, Key=old_copy_key)
        except Exception as ex:
            print(f"Failed to delete old copy {old_copy_key}: {ex}")

        table.delete_item(
            Key={
                "source_key": item["source_key"],
                "copy_sort": item["copy_sort"],
            }
        )


def _handle_delete(source_key: str) -> None:
    """Mark owned copies as disowned; cleaner removes them later."""
    now = int(time.time())

    resp = table.query(
        KeyConditionExpression=Key("source_key").eq(source_key),
        FilterExpression=Attr("copy_status").eq("OWNED"),
    )
    items = resp.get("Items", [])

    while "LastEvaluatedKey" in resp:
        resp = table.query(
            KeyConditionExpression=Key("source_key").eq(source_key),
            FilterExpression=Attr("copy_status").eq("OWNED"),
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp.get("Items", []))

    for item in items:
        table.update_item(
            Key={
                "source_key": item["source_key"],
                "copy_sort": item["copy_sort"],
            },
            UpdateExpression="SET copy_status = :s, disowned_at = :d",
            ExpressionAttributeValues={
                ":s": "DISOWNED",
                ":d": now,
            },
        )


def _extract_events(event: dict) -> list[tuple[str, str]]:
    """Normalize S3 notification and EventBridge payloads into (event_name, key)."""
    normalized: list[tuple[str, str]] = []

    # S3 notification format (Records list)
    if "Records" in event:
        for record in event.get("Records", []):
            event_name = record.get("eventName", "")
            key = _decode_key(record["s3"]["object"]["key"])
            normalized.append((event_name, key))
        return normalized

    # EventBridge S3 format
    detail_type = event.get("detail-type", "")
    detail = event.get("detail", {})
    key = _decode_key(detail.get("object", {}).get("key", ""))
    if not key:
        return normalized

    if detail_type == "Object Created":
        normalized.append(("ObjectCreated:EventBridge", key))
    elif detail_type == "Object Deleted":
        normalized.append(("ObjectRemoved:EventBridge", key))

    return normalized


def lambda_handler(event, context):
    """Dispatch S3 create/remove events to PUT/DELETE handlers."""
    for event_name, source_key in _extract_events(event):

        if event_name.startswith("ObjectCreated"):
            _handle_put(source_key)
        elif event_name.startswith("ObjectRemoved"):
            _handle_delete(source_key)

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Replicator processed event"}),
    }
