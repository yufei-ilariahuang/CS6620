import boto3
import matplotlib
matplotlib.use("Agg")  # non-interactive backend, required in Lambda
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timezone, timedelta
from io import BytesIO

BUCKET_NAME = "testbucket-lia-hw2"
TABLE_NAME  = "S3-object-size-history"
REGION      = "us-west-1"

s3  = boto3.client("s3",  region_name=REGION)
ddb = boto3.resource("dynamodb", region_name=REGION)


def lambda_handler(event, context):
    table = ddb.Table(TABLE_NAME)

    # ── Query all items for this bucket (no scan) ─────────────────────────────
    resp = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("bucketName").eq(BUCKET_NAME)
    )
    items = resp.get("Items", [])

    if not items:
        return {"statusCode": 200, "body": "No data to plot yet."}

    # ── Parse and sort all items by timestamp ─────────────────────────────────
    for item in items:
        item["_dt"] = datetime.fromisoformat(item["timeStamp"])
    items.sort(key=lambda x: x["_dt"])

    all_times = [i["_dt"] for i in items]
    all_sizes = [int(i["totalSize"]) for i in items]

    # ── Filter last 10 seconds ────────────────────────────────────────────────
    now        = max(all_times)
    cutoff     = now - timedelta(seconds=10)
    recent     = [(t, s) for t, s in zip(all_times, all_sizes) if t >= cutoff]

    if recent:
        r_times, r_sizes = zip(*recent)
    else:
        r_times, r_sizes = all_times[-1:], all_sizes[-1:]  # fallback: last point

    # ── Max size across ALL items ─────────────────────────────────────────────
    max_size = max(all_sizes)

    # ── Plot ──────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(r_times, r_sizes, marker="o", label="Total size (last 10s)")
    ax.axhline(y=max_size, color="red", linestyle="--", label=f"Max size ever: {max_size} bytes")
    
    # force X axis to always span exactly 10 seconds with 10 marks
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

    # ── Save plot to S3 ───────────────────────────────────────────────────────
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