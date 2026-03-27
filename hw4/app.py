#!/usr/bin/env python3
"""
HW4 – SNS/SQS Fanout + CloudWatch Metrics + Alarms
Entry point for CDK application.
"""
import os

import aws_cdk as cdk

from cdk.storage_stack import StorageStack
from cdk.compute_stack import ComputeStack
from cdk.driver_stack  import DriverStack

app = cdk.App()

env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION", "us-west-1"),
)

# Stack 1: S3 bucket + DynamoDB table (stateful)
storage = StorageStack(app, "StorageStack", env=env)

# Stack 2: S3 + SNS + SQS + Lambdas + CloudWatch metrics/alarms
compute = ComputeStack(app, "ComputeStack", storage=storage, env=env)

# Stack 3: driver lambda (orchestrator)
driver  = DriverStack(app, "DriverStack",  compute=compute, env=env)

app.synth()
