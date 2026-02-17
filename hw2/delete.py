import boto3
from botocore.exceptions import ClientError

BUCKET_NAME = "testbucket-lia-hw2"
TABLE_NAME  = "S3-object-size-history"
REGION      = "us-west-1"

s3     = boto3.client("s3",      region_name=REGION)
ddb    = boto3.client("dynamodb", region_name=REGION)
lamb   = boto3.client("lambda",  region_name=REGION)
apigw  = boto3.client("apigatewayv2", region_name=REGION)


# ── S3: empty and delete bucket ───────────────────────────────────────────────
def delete_bucket():
    try:
        # delete all objects first
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=BUCKET_NAME):
            objects = [{"Key": o["Key"]} for o in page.get("Contents", [])]
            if objects:
                s3.delete_objects(Bucket=BUCKET_NAME, Delete={"Objects": objects})
        s3.delete_bucket(Bucket=BUCKET_NAME)
        print(f"[OK] Deleted S3 bucket '{BUCKET_NAME}'")
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucket":
            print(f"[SKIP] S3 bucket '{BUCKET_NAME}' not found")
        else:
            raise


# ── DynamoDB: delete table ────────────────────────────────────────────────────
def delete_table():
    try:
        ddb.delete_table(TableName=TABLE_NAME)
        waiter = ddb.get_waiter("table_not_exists")
        waiter.wait(TableName=TABLE_NAME)
        print(f"[OK] Deleted DynamoDB table '{TABLE_NAME}'")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"[SKIP] DynamoDB table '{TABLE_NAME}' not found")
        else:
            raise


# ── Lambda: delete functions (keep layers) ────────────────────────────────────
def delete_lambdas():
    for name in ["size-tracking", "plotting", "driver"]:
        try:
            lamb.delete_function(FunctionName=name)
            print(f"[OK] Deleted Lambda function '{name}'")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                print(f"[SKIP] Lambda '{name}' not found")
            else:
                raise


# ── API Gateway: delete all HTTP APIs ─────────────────────────────────────────
def delete_apis():
    try:
        apis = apigw.get_apis().get("Items", [])
        if not apis:
            print("[SKIP] No API Gateway APIs found")
        for api in apis:
            apigw.delete_api(ApiId=api["ApiId"])
            print(f"[OK] Deleted API Gateway '{api['Name']}' ({api['ApiId']})")
    except ClientError as e:
        print(f"[ERROR] API Gateway cleanup failed: {e}")


if __name__ == "__main__":
    delete_bucket()
    delete_table()
    delete_lambdas()
    delete_apis()
    print("\nCleanup done. Matplotlib layer kept.")