import boto3
import time
from botocore.exceptions import ClientError

# Configuration
ACCOUNT_ID = "389226936064"
REGION = "us-east-2"
DEV_ROLE_NAME = "Dev"
BUCKET_NAME = f"hw1-bucket-{ACCOUNT_ID}"

def assume_role(role_name):
    """Helper function to assume a role and return credentials"""
    sts = boto3.client('sts', region_name=REGION)
    
    role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
    
    try:
        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"{role_name}-session"
        )
        
        credentials = response['Credentials']
        print(f"✓ Assumed role: {role_name}")
        
        return credentials
    except ClientError as e:
        print(f"! Error assuming role {role_name}: {e}")
        raise

def create_s3_resources():
    """Assume Dev role and create S3 bucket and objects"""
    print("=== Assuming Dev Role ===")
    credentials = assume_role(DEV_ROLE_NAME)
    
    # Create S3 client with assumed role credentials
    s3 = boto3.client(
        's3',
        region_name=REGION,
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    
    # Create bucket
    try:
        s3.create_bucket(
            Bucket=BUCKET_NAME,
            CreateBucketConfiguration={'LocationConstraint': REGION}
        )
        print(f"✓ Created bucket: {BUCKET_NAME}")
        time.sleep(2)  # Wait for bucket to be ready
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            print(f"✓ Bucket already exists: {BUCKET_NAME}")
        else:
            raise
    
    # Upload assignment1.txt from local file
    try:
        s3.upload_file(
            'assignment1.txt',
            BUCKET_NAME,
            'assignment1.txt'
        )
        print(f"✓ Uploaded object: assignment1.txt")
    except FileNotFoundError:
        print(f"! Error: assignment1.txt not found in current directory")
        raise
    
    # Upload assignment2.txt from local file
    try:
        s3.upload_file(
            'assignment2.txt',
            BUCKET_NAME,
            'assignment2.txt'
        )
        print(f"✓ Uploaded object: assignment2.txt")
    except FileNotFoundError:
        print(f"! Error: assignment2.txt not found in current directory")
        raise
    
    # Upload recording1.jpg from local file
    try:
        s3.upload_file(
            'recording1.jpg',
            BUCKET_NAME,
            'recording1.jpg'
        )
        print(f"✓ Uploaded object: recording1.jpg")
    except FileNotFoundError:
        print(f"! Error: recording1.jpg not found in current directory")
        raise

def main():
    print("=== Creating S3 Resources as Dev ===\n")
    
    try:
        create_s3_resources()
        print("\n=== S3 Resources Created Successfully! ===")
        print(f"Bucket: {BUCKET_NAME}")
        print("Objects: assignment1.txt, assignment2.txt, recording1.jpg")
    except Exception as e:
        print(f"\n!!! Error occurred: {e}")
        raise

if __name__ == "__main__":
    main()