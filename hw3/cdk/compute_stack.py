from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    CfnOutput,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_iam as iam,
)
from constructs import Construct
from .storage_stack import StorageStack


class ComputeStack(Stack):
    """
    Stack 2 – S3 bucket + event-driven compute + REST API.

    The S3 bucket lives here (not in StorageStack) so that the Lambda event
    notification and the bucket are in the same stack, avoiding a CDK
    cross-stack cyclic dependency.

    - TestBucket:            S3 bucket; triggers size-tracking on object events
    - size-tracking lambda:  records bucket size to DynamoDB on every S3 event
    - plotting lambda:       matplotlib layer, Function URL (REST API, no auth)
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        storage: StorageStack,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table = storage.table

        # ── S3 bucket (TestBucket) ─────────────────────────────────────────────
        # Co-located with the Lambda so CDK can wire the event notification
        # without a cross-stack cycle.
        self.bucket = s3.Bucket(
            self, "TestBucket",
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ── Matplotlib layer (pre-built for us-west-1) ────────────────────────
        matplotlib_layer = lambda_.LayerVersion.from_layer_version_arn(
            self, "MatplotlibLayer",
            "arn:aws:lambda:us-west-1:389226936064:layer:matplotlib-layer:3",
        )

        # ── size-tracking lambda ──────────────────────────────────────────────
        size_tracking_fn = lambda_.Function(
            self, "SizeTrackingFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="size_tracking_lambda.lambda_handler",
            code=lambda_.Code.from_asset("lambda/"),
            environment={
                "BUCKET_NAME": self.bucket.bucket_name,
                "TABLE_NAME":  table.table_name,
                "REGION":      self.region,
            },
            timeout=Duration.seconds(30),
        )

        self.bucket.grant_read(size_tracking_fn)   # list + get objects
        table.grant_write_data(size_tracking_fn)   # put_item

        # S3 → Lambda notifications (create AND delete) — same-stack, no cycle
        for event_type in (
            s3.EventType.OBJECT_CREATED,
            s3.EventType.OBJECT_REMOVED,
        ):
            self.bucket.add_event_notification(
                event_type,
                s3n.LambdaDestination(size_tracking_fn),
            )

        # ── plotting lambda ───────────────────────────────────────────────────
        plotting_fn = lambda_.Function(
            self, "PlottingFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="plotting_lambda.lambda_handler",
            code=lambda_.Code.from_asset("lambda/"),
            layers=[matplotlib_layer],
            environment={
                "BUCKET_NAME": self.bucket.bucket_name,
                "TABLE_NAME":  table.table_name,
                "REGION":      self.region,
            },
            timeout=Duration.seconds(30),
        )

        self.bucket.grant_read_write(plotting_fn)  # put plot object
        table.grant_read_data(plotting_fn)         # query size history

        # listing ALL buckets to compute global max requires a * resource
        plotting_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:ListAllMyBuckets"],
                resources=["*"],
            )
        )

        # Function URL = REST API endpoint (no auth, matches hw2 behaviour)
        fn_url = plotting_fn.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.NONE,
        )
        self.plotting_url: str = fn_url.url

        # ── Outputs ───────────────────────────────────────────────────────────
        CfnOutput(self, "BucketName",        value=self.bucket.bucket_name)
        CfnOutput(self, "PlottingFunctionUrl", value=fn_url.url)
