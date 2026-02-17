import boto3
from botocore.exceptions import ClientError

# Configuration
ACCOUNT_ID = "389226936064"
REGION = "us-east-2"
USER_ROLE_NAME = "User"
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

def list_and_calculate():
    """Assume User role and list/calculate size of assignment objects"""
    print("=== Assuming User Role ===")
    credentials = assume_role(USER_ROLE_NAME)
    
    # Create S3 client with assumed role credentials
    s3 = boto3.client(
        's3',
        region_name=REGION,
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    
    # List objects with prefix "assignment"
    try:
        response = s3.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix='assignment'
        )
        
        if 'Contents' in response:
            total_size = 0
            print(f"\n✓ Objects with prefix 'assignment':")
            for obj in response['Contents']:
                print(f"  - {obj['Key']}: {obj['Size']} bytes")
                total_size += obj['Size']
            
            print(f"\n✓ Total size of 'assignment' objects: {total_size} bytes")
            return total_size
        else:
            print("! No objects found with prefix 'assignment'")
            return 0
            
    except ClientError as e:
        print(f"! Error listing objects: {e}")
        raise

def main():
    print("=== Listing Objects as User ===\n")
    
    try:
        list_and_calculate()
        print("\n=== Task Completed Successfully! ===")
    except Exception as e:
        print(f"\n!!! Error occurred: {e}")
        raise

if __name__ == "__main__":
    main()