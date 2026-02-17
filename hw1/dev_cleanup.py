import boto3
from botocore.exceptions import ClientError

# Configuration
ACCOUNT_ID = "389226936064"
REGION = "us-east-2"
DEV_ROLE_NAME = "Dev"
USER_ROLE_NAME = "User"
IAM_USER_NAME = "hw1-user"
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

def cleanup_s3():
    """Assume Dev role and delete all S3 objects and bucket"""
    print("=== Assuming Dev Role for S3 Cleanup ===")
    
    try:
        credentials = assume_role(DEV_ROLE_NAME)
        
        # Create S3 client with assumed role credentials
        s3 = boto3.client(
            's3',
            region_name=REGION,
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
        
        # List and delete all objects
        try:
            response = s3.list_objects_v2(Bucket=BUCKET_NAME)
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    s3.delete_object(Bucket=BUCKET_NAME, Key=obj['Key'])
                    print(f"✓ Deleted object: {obj['Key']}")
            
            # Delete the bucket
            s3.delete_bucket(Bucket=BUCKET_NAME)
            print(f"✓ Deleted bucket: {BUCKET_NAME}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                print(f"✓ Bucket {BUCKET_NAME} does not exist (already deleted)")
            else:
                print(f"! Error during S3 cleanup: {e}")
                
    except Exception as e:
        print(f"! Could not assume Dev role or clean up S3: {e}")

def cleanup_iam():
    """Delete IAM user and roles"""
    print("\n=== Cleaning Up IAM Resources ===")
    iam = boto3.client('iam', region_name=REGION)
    
    # Delete IAM user
    try:
        # Delete user's inline policies first
        try:
            iam.delete_user_policy(
                UserName=IAM_USER_NAME,
                PolicyName="AssumeRolePolicy"
            )
            print(f"✓ Deleted user inline policy: AssumeRolePolicy")
        except ClientError:
            pass
        
        # Detach managed policies from user
        try:
            iam.detach_user_policy(
                UserName=IAM_USER_NAME,
                PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
            )
            print(f"✓ Detached AdministratorAccess from user")
        except ClientError:
            pass
        
        # Delete access keys
        try:
            keys_response = iam.list_access_keys(UserName=IAM_USER_NAME)
            for key in keys_response['AccessKeyMetadata']:
                iam.delete_access_key(
                    UserName=IAM_USER_NAME,
                    AccessKeyId=key['AccessKeyId']
                )
                print(f"✓ Deleted access key: {key['AccessKeyId']}")
        except ClientError:
            pass
        
        # Delete the user
        iam.delete_user(UserName=IAM_USER_NAME)
        print(f"✓ Deleted IAM user: {IAM_USER_NAME}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print(f"✓ IAM user {IAM_USER_NAME} does not exist (already deleted)")
        else:
            print(f"! Error deleting IAM user: {e}")
    
    # Delete Dev role
    try:
        # Detach managed policies
        try:
            iam.detach_role_policy(
                RoleName=DEV_ROLE_NAME,
                PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess'
            )
            print(f"✓ Detached AmazonS3FullAccess from Dev role")
        except ClientError:
            pass
        
        # Delete the role
        iam.delete_role(RoleName=DEV_ROLE_NAME)
        print(f"✓ Deleted IAM role: {DEV_ROLE_NAME}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print(f"✓ IAM role {DEV_ROLE_NAME} does not exist (already deleted)")
        else:
            print(f"! Error deleting Dev role: {e}")
    
    # Delete User role
    try:
        # Delete inline policies first
        try:
            iam.delete_role_policy(
                RoleName=USER_ROLE_NAME,
                PolicyName="S3ReadOnlyPolicy"
            )
            print(f"✓ Deleted User role inline policy")
        except ClientError:
            pass
        
        # Delete the role
        iam.delete_role(RoleName=USER_ROLE_NAME)
        print(f"✓ Deleted IAM role: {USER_ROLE_NAME}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print(f"✓ IAM role {USER_ROLE_NAME} does not exist (already deleted)")
        else:
            print(f"! Error deleting User role: {e}")

def main():
    print("=== Cleaning Up All AWS Resources ===\n")
    
    # Clean up S3 resources (requires assuming Dev role)
    cleanup_s3()
    
    # Clean up IAM resources (uses your base credentials)
    cleanup_iam()
    
    print("\n=== Cleanup Complete! ===")
    print("All S3 objects, buckets, IAM users, and roles have been deleted.")

if __name__ == "__main__":
    main()