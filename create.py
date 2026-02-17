import boto3
from botocore.exceptions import ClientError

BUCKET_NAME = "TestBucket"          # must be globally unique — change suffix if needed
TABLE_NAME  = "S3-object-size-history"
REGION      = "us-east-1"           # change to your region

s3  = boto3.client("s3",  region_name=REGION)
ddb = boto3.client("dynamodb", region_name=REGION)


# ── 1. Create S3 bucket ───────────────────────────────────────────────────────
def create_bucket():
    try:
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=BUCKET_NAME)
        else:
            s3.create_bucket(
                Bucket=BUCKET_NAME,
                CreateBucketConfiguration={"LocationConstraint": REGION},
            )
        print(f"[OK] S3 bucket '{BUCKET_NAME}' created.")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            print(f"[SKIP] S3 bucket '{BUCKET_NAME}' already exists.")
        else:
            raise


# ── 2. Create DynamoDB table ──────────────────────────────────────────────────
def create_table():
    try:
        ddb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "bucketName", "KeyType": "HASH"},   # partition key
                {"AttributeName": "timeStamp",  "KeyType": "RANGE"},  # sort key
            ],
            AttributeDefinitions=[
                {"AttributeName": "bucketName", "AttributeType": "S"},
                {"AttributeName": "timeStamp",  "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        waiter = ddb.get_waiter("table_exists")
        waiter.wait(TableName=TABLE_NAME)
        print(f"[OK] DynamoDB table '{TABLE_NAME}' created and active.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"[SKIP] DynamoDB table '{TABLE_NAME}' already exists.")
        else:
            raise


if __name__ == "__main__":
    create_bucket()
    create_table()
    print("\nDone. Verify in AWS Console:")
    print(f"  S3  → {BUCKET_NAME}  (should be empty)")
    print(f"  DDB → {TABLE_NAME}  (should be empty)")