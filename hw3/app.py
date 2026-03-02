#!/usr/bin/env python3
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

# Stack 1: S3 bucket + DynamoDB table (stateful, deploy once)
storage = StorageStack(app, "StorageStack", env=env)

# Stack 2: size-tracking lambda + plotting lambda + REST API
compute = ComputeStack(app, "ComputeStack", storage=storage, env=env)

# Stack 3: driver lambda (test orchestrator)
driver  = DriverStack(app, "DriverStack",  compute=compute, env=env)

app.synth()
