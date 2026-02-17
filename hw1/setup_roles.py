import boto3
import json
from botocore.exceptions import ClientError

# Configuration
ACCOUNT_ID = "389226936064"
REGION = "us-east-2"
DEV_ROLE_NAME = "Dev"
USER_ROLE_NAME = "User"
IAM_USER_NAME = "hw1-user"

def create_iam_user_with_keys():
    """Step 1: Create IAM user with access keys"""
    iam = boto3.client('iam', region_name=REGION)
    
    # Create IAM user
    try:
        user = iam.create_user(UserName=IAM_USER_NAME)
        print(f"✓ Created IAM user: {user['User']['Arn']}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"✓ IAM user already exists")
        else:
            raise
    
    # Attach AdministratorAccess policy to user (for homework purposes)
    try:
        iam.attach_user_policy(
            UserName=IAM_USER_NAME,
            PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
        )
        print(f"✓ Attached AdministratorAccess policy to user")
    except ClientError as e:
        print(f"✓ Policy already attached")
    
    # Create access keys for the user
    try:
        response = iam.create_access_key(UserName=IAM_USER_NAME)
        access_key = response['AccessKey']
        
        print(f"\n{'='*60}")
        print(f"⚠️  IMPORTANT: Save these credentials!")
        print(f"{'='*60}")
        print(f"Access Key ID:     {access_key['AccessKeyId']}")
        print(f"Secret Access Key: {access_key['SecretAccessKey']}")
        print(f"{'='*60}")
        print(f"\nRun this command to configure AWS CLI:")
        print(f"  aws configure --profile hw1")
        print(f"\nThen set the profile:")
        print(f"  export AWS_PROFILE=hw1")
        print(f"{'='*60}\n")
        
        # Save to file for convenience
        with open('hw1_credentials.txt', 'w') as f:
            f.write(f"Access Key ID: {access_key['AccessKeyId']}\n")
            f.write(f"Secret Access Key: {access_key['SecretAccessKey']}\n")
            f.write(f"\nTo use these credentials:\n")
            f.write(f"  aws configure --profile hw1\n")
            f.write(f"  export AWS_PROFILE=hw1\n")
        
        print(f"✓ Credentials saved to: hw1_credentials.txt")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'LimitExceeded':
            print(f"! User already has 2 access keys (AWS limit)")
            print(f"  Delete an old key in AWS Console first")
        else:
            print(f"! Error creating access key: {e}")

def create_iam_roles():
    """Step 2: Create IAM roles with appropriate policies"""
    iam = boto3.client('iam', region_name=REGION)
    
    # Trust policy for both roles (allows the IAM user to assume these roles)
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{ACCOUNT_ID}:user/{IAM_USER_NAME}"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Create Dev role
    try:
        dev_role = iam.create_role(
            RoleName=DEV_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role with full S3 access"
        )
        print(f"✓ Created Dev role: {dev_role['Role']['Arn']}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"✓ Dev role already exists")
        else:
            raise
    
    # Attach full S3 access policy to Dev role
    try:
        iam.attach_role_policy(
            RoleName=DEV_ROLE_NAME,
            PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess'
        )
        print(f"✓ Attached AmazonS3FullAccess to Dev role")
    except ClientError as e:
        print(f"✓ Policy already attached to Dev role")
    
    # Create User role
    try:
        user_role = iam.create_role(
            RoleName=USER_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role with read-only S3 access"
        )
        print(f"✓ Created User role: {user_role['Role']['Arn']}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"✓ User role already exists")
        else:
            raise
    
    # Create custom read-only policy for User role
    read_only_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:ListAllMyBuckets",
                    "s3:GetBucketLocation",
                    "s3:GetObject"
                ],
                "Resource": "*"
            }
        ]
    }
    
    # Create and attach inline policy to User role
    try:
        iam.put_role_policy(
            RoleName=USER_ROLE_NAME,
            PolicyName="S3ReadOnlyPolicy",
            PolicyDocument=json.dumps(read_only_policy)
        )
        print(f"✓ Attached S3 read-only policy to User role")
    except ClientError as e:
        print(f"! Error attaching policy to User role: {e}")

def main():
    print("=== Setting Up IAM User and Roles ===\n")
    
    print("Step 1: Creating IAM user with access keys...")
    create_iam_user_with_keys()
    
    print("\nStep 2: Creating IAM roles with policies...")
    create_iam_roles()
    
    print("\n=== Setup Complete! ===")
    print(f"\n⚠️  NEXT STEPS:")
    print(f"1. Configure AWS CLI with the new credentials:")
    print(f"   aws configure --profile hw1")
    print(f"2. Set the profile:")
    print(f"   export AWS_PROFILE=hw1")
    print(f"3. Run the next script:")
    print(f"   python dev_create.py")

if __name__ == "__main__":
    main()