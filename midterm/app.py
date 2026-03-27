#!/usr/bin/env python3
"""CDK app entrypoint for the midterm backup system."""

import os

import aws_cdk as cdk

from cdk.storage_stack import StorageStack
from cdk.replicator_stack import ReplicatorStack
from cdk.cleaner_stack import CleanerStack

app = cdk.App()

env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION", "us-west-1"),
)

storage = StorageStack(app, "MidtermStorageStack", env=env)
replicator = ReplicatorStack(app, "MidtermReplicatorStack", storage=storage, env=env)
cleaner = CleanerStack(app, "MidtermCleanerStack", storage=storage, env=env)

app.synth()
