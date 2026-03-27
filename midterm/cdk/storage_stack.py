from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    Stack,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
)
from constructs import Construct


class StorageStack(Stack):
    """Stateful resources: source/destination buckets and mapping table."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Source bucket receives user object PUT/DELETE events.
        self.source_bucket = s3.Bucket(
            self,
            "SourceBucket",
            versioned=False,
            event_bridge_enabled=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Destination bucket stores replicated object copies.
        self.destination_bucket = s3.Bucket(
            self,
            "DestinationBucket",
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Base table indexes copies by original source object key.
        self.table = dynamodb.Table(
            self,
            "ObjectCopyMapTable",
            partition_key=dynamodb.Attribute(
                name="source_key",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="copy_sort",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # GSI supports cleaner query by disowned status and age.
        self.table.add_global_secondary_index(
            index_name="status-disowned-at-index",
            partition_key=dynamodb.Attribute(
                name="copy_status",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="disowned_at",
                type=dynamodb.AttributeType.NUMBER,
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        CfnOutput(self, "SourceBucketName", value=self.source_bucket.bucket_name)
        CfnOutput(self, "DestinationBucketName", value=self.destination_bucket.bucket_name)
        CfnOutput(self, "TableName", value=self.table.table_name)
