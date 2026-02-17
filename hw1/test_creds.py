import boto3
import os

print("Environment variables:")
for key in os.environ:
    if 'AWS' in key.upper():
        print(f"  {key} = {os.environ[key][:20]}...")

print("\nBoto3 credentials:")
session = boto3.Session()
credentials = session.get_credentials()
if credentials:
    print(f"  Access Key: {credentials.access_key[:20]}...")
    print(f"  Method: {credentials.method}")
else:
    print("  No credentials found!")

print("\nTrying STS call:")
try:
    sts = boto3.client('sts')
    identity = sts.get_caller_identity()
    print(f"  Success! Account: {identity['Account']}")
except Exception as e:
    print(f"  Failed: {e}")
