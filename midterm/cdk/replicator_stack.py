from aws_cdk import (
    Duration,
    Stack,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_,
)
from constructs import Construct

from .storage_stack import StorageStack


class ReplicatorStack(Stack):
    """Replicator Lambda and S3 event wiring."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        storage: StorageStack,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Handles source object create/delete events.
        self.replicator_function = lambda_.Function(
            self,
            "ReplicatorFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="replicator_lambda.lambda_handler",
            code=lambda_.Code.from_asset("lambda/"),
            timeout=Duration.seconds(60),
            environment={
                "SOURCE_BUCKET": storage.source_bucket.bucket_name,
                "DEST_BUCKET": storage.destination_bucket.bucket_name,
                "TABLE_NAME": storage.table.table_name,
                "STATUS_INDEX_NAME": "status-disowned-at-index",
            },
        )

        # Replicator reads source, writes destination, and updates DynamoDB.
        storage.source_bucket.grant_read(self.replicator_function)
        storage.destination_bucket.grant_read_write(self.replicator_function)
        storage.table.grant_read_write_data(self.replicator_function)

        # Trigger Replicator from EventBridge S3 object-level events.
        events.Rule(
            self,
            "ReplicatorS3EventsRule",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created", "Object Deleted"],
                detail={
                    "bucket": {
                        "name": [storage.source_bucket.bucket_name],
                    }
                },
            ),
            targets=[targets.LambdaFunction(self.replicator_function)],
        )
