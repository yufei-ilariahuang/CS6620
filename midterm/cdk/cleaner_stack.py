from aws_cdk import (
    Duration,
    Stack,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_,
)
from constructs import Construct

from .storage_stack import StorageStack


class CleanerStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        storage: StorageStack,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Periodic cleanup worker for disowned destination copies.
        self.cleaner_function = lambda_.Function(
            self,
            "CleanerFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="cleaner_lambda.lambda_handler",
            code=lambda_.Code.from_asset("lambda/"),
            timeout=Duration.seconds(60),
            environment={
                "DEST_BUCKET": storage.destination_bucket.bucket_name,
                "TABLE_NAME": storage.table.table_name,
                "STATUS_INDEX_NAME": "status-disowned-at-index",
                "DISOWNED_AGE_SECONDS": "10",
            },
        )

        # Cleaner must delete S3 objects and update DynamoDB state.
        storage.destination_bucket.grant_read_write(self.cleaner_function)
        storage.table.grant_read_write_data(self.cleaner_function)

        # Run every minute as required by the assignment spec.
        events.Rule(
            self,
            "CleanerScheduleRule",
            schedule=events.Schedule.rate(Duration.minutes(1)),
            targets=[targets.LambdaFunction(self.cleaner_function)],
        )
