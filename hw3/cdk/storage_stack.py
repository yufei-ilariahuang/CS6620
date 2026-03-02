from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class StorageStack(Stack):
    """
    Stack 1 – stateful resources only.
    Creates the DynamoDB size-history table with a GSI so rows can also be
    queried by timeStamp alone (cross-bucket view).

    NOTE: The S3 bucket lives in ComputeStack alongside the Lambda event
    notification to avoid a CDK cross-stack cyclic dependency.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── DynamoDB table  PK=bucketName  SK=timeStamp ───────────────────────
        self.table = dynamodb.Table(
            self, "SizeHistoryTable",
            partition_key=dynamodb.Attribute(
                name="bucketName", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timeStamp", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # GSI – enables querying / scanning by timeStamp across all buckets
        self.table.add_global_secondary_index(
            index_name="timeStamp-index",
            partition_key=dynamodb.Attribute(
                name="timeStamp", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # ── Outputs ───────────────────────────────────────────────────────────
        CfnOutput(self, "TableName", value=self.table.table_name)
