from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
)
from constructs import Construct
from .compute_stack import ComputeStack


class DriverStack(Stack):
    """
    Stack 3 – test orchestrator.

    The driver lambda runs the full hw2 sequence (put / update / delete /
    put / delete) and then calls the plotting REST API.  It is deployed
    separately so it can be removed or re-run without touching stateful
    infrastructure.
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
            timeout=Duration.seconds(60),   # sleeps ~12 s + plotting call
        )

        bucket.grant_read_write(driver_fn)  # put / delete objects in TestBucket
