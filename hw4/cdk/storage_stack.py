"""
Stack 1 – Stateful Resources (DynamoDB)
"""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class StorageStack(Stack):
    """
    DynamoDB size-history table with GSI.
    
    - PK: bucketName
    - SK: timeStamp
    - GSI: query by timeStamp across all buckets
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB table
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

        # GSI for cross-bucket timeStamp queries
        self.table.add_global_secondary_index(
            index_name="timeStamp-index",
            partition_key=dynamodb.Attribute(
                name="timeStamp", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        CfnOutput(self, "TableName", value=self.table.table_name)
