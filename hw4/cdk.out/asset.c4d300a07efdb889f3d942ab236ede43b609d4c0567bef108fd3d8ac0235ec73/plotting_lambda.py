"""
Plotting Lambda – Visualization
Generates a matplotlib plot of bucket size over last 10 seconds.
Saves plot to S3.
"""
import os
import boto3
import matplotlib
matplotlib.use("Agg")  # non-interactive backend required in Lambda
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timezone, timedelta
from io import BytesIO

BUCKET_NAME = os.environ["BUCKET_NAME"]
TABLE_NAME  = os.environ["TABLE_NAME"]
REGION      = os.environ["REGION"]

s3  = boto3.client("s3",  region_name=REGION)
ddb = boto3.resource("dynamodb", region_name=REGION)


def lambda_handler(event, context):
    """
    Query DynamoDB for bucket size history.
    Plot last 10 seconds.
    Save plot to S3 as 'plot'.
    """
    
    table = ddb.Table(TABLE_NAME)

    # Query all items for TestBucket
    resp = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("bucketName").eq(BUCKET_NAME)
    )
    items = resp.get("Items", [])

    if not items:
        return {"statusCode": 200, "body": "No data to plot yet."}

    # Parse and sort by timestamp
    for item in items:
        item["_dt"] = datetime.fromisoformat(item["timeStamp"])
    items.sort(key=lambda x: x["_dt"])

    all_times = [i["_dt"] for i in items]
    all_sizes = [int(i["totalSize"]) for i in items]

    # Filter last 10 seconds for line plot
    now    = max(all_times)
    cutoff = now - timedelta(seconds=10)
    recent = [(t, s) for t, s in zip(all_times, all_sizes) if t >= cutoff]

    if recent:
        r_times, r_sizes = zip(*recent)
    else:
        r_times, r_sizes = all_times[-1:], all_sizes[-1:]

    # Max size across all buckets
    all_bucket_names = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    global_max = 0
    for bkt in all_bucket_names:
        bkt_resp = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("bucketName").eq(bkt),
            ProjectionExpression="totalSize"
        )
        bkt_items = bkt_resp.get("Items", [])
        while "LastEvaluatedKey" in bkt_resp:
            bkt_resp = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key("bucketName").eq(bkt),
                ProjectionExpression="totalSize",
                ExclusiveStartKey=bkt_resp["LastEvaluatedKey"]
            )
            bkt_items.extend(bkt_resp.get("Items", []))
        if bkt_items:
            bkt_max = max(int(r["totalSize"]) for r in bkt_items)
            global_max = max(global_max, bkt_max)

    max_size = global_max if global_max > 0 else max(all_sizes)

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(r_times, r_sizes, marker="o", label="Total size (last 10s)")
    ax.axhline(y=max_size, color="red", linestyle="--", label=f"Max size ever: {max_size} bytes")
    
    # X-axis: exactly 10 seconds with 10 marks
    x_end   = now
    x_start = x_end - timedelta(seconds=10)
    ax.set_xlim(x_start, x_end)
    ax.xaxis.set_major_locator(mdates.SecondLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))

    ax.set_xlabel("Timestamp (UTC)")
    ax.set_ylabel("Size (bytes)")
    ax.set_title("S3 Bucket Size History (Last 10 Seconds)")
    fig.autofmt_xdate()
    ax.legend()
    plt.tight_layout()

    # Save plot to S3
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)

    s3.put_object(Bucket=BUCKET_NAME, Key="plot", Body=buf, ContentType="image/png")
    print("[OK] Plot saved to S3 as 'plot'")

    return {
        "statusCode": 200,
        "body": "Plot generated and saved to S3."
    }
