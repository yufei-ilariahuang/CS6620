"""
Stack 3 – Driver Lambda (Orchestrator)
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
)
from constructs import Construct
from .compute_stack import ComputeStack


class DriverStack(Stack):
    """
    Test orchestrator.
    
    Runs the hw4 sequence:
    1. Create assignment1.txt (19 bytes)
    2. Create assignment2.txt (28 bytes) → alarm fires, Cleaner deletes it
    3. Create assignment3.txt (2 bytes) → alarm fires, Cleaner deletes assignment1.txt
    4. Call plotting REST API
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        compute: ComputeStack,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = compute.bucket

        driver_fn = lambda_.Function(
            self, "DriverFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="driver_lambda.lambda_handler",
            code=lambda_.Code.from_asset("lambda/"),
            environment={
                "BUCKET_NAME":  bucket.bucket_name,
                "REGION":       self.region,
                "PLOTTING_URL": compute.plotting_url,
            },
            timeout=Duration.seconds(120),
        )

        bucket.grant_read_write(driver_fn)
