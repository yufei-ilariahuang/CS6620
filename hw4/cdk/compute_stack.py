"""
Stack 2 – Event Processing (SNS/SQS/Lambda/CloudWatch)
"""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    CfnOutput,
    aws_lambda as lambda_,
    aws_lambda_event_sources as lambda_event_sources,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_sqs as sqs,
    aws_iam as iam,
    aws_logs as logs,
    aws_cloudwatch as cw,
)
from constructs import Construct
from .storage_stack import StorageStack


class ComputeStack(Stack):
    """
    S3 → SNS → SQS → Lambdas → DynamoDB + CloudWatch.
    
    Flow:
    - S3 bucket EventBridge notifications → SNS topic
    - SNS topic fans out to 2 SQS queues
    - Queue 1 → size-tracking lambda → DynamoDB
    - Queue 2 → logging lambda → CloudWatch logs
    - CloudWatch metric filter extracts size_delta → TotalObjectSize metric
    - CloudWatch alarm (SUM > 20) → Cleaner lambda
    - Cleaner lambda deletes largest object
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

        # ── S3 Bucket ──────────────────────────────────────────────────────────
        self.bucket = s3.Bucket(
            self, "TestBucket",
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ── SNS Topic (fanout center) ──────────────────────────────────────────
        sns_topic = sns.Topic(
            self, "S3EventTopic",
            display_name="S3 Event Fanout Topic",
        )

        # Enable S3 → SNS via EventBridge
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.SnsDestination(sns_topic),
        )
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_REMOVED,
            s3n.SnsDestination(sns_topic),
        )

        # ── SQS Queues (2 consumers) ──────────────────────────────────────────
        size_tracking_queue = sqs.Queue(
            self, "SizeTrackingQueue",
            visibility_timeout=Duration.seconds(60),
            retention_period=Duration.seconds(300),
        )

        logging_queue = sqs.Queue(
            self, "LoggingQueue",
            visibility_timeout=Duration.seconds(60),
            retention_period=Duration.seconds(300),
        )

        # SNS → SQS subscriptions
        sns_topic.add_subscription(
            sns_subs.SqsSubscription(size_tracking_queue)
        )
        sns_topic.add_subscription(
            sns_subs.SqsSubscription(logging_queue)
        )

        # ── Matplotlib Layer ───────────────────────────────────────────────────
        matplotlib_layer = lambda_.LayerVersion.from_layer_version_arn(
            self, "MatplotlibLayer",
            "arn:aws:lambda:us-west-1:389226936064:layer:matplotlib-layer:3",
        )

        # ── Size-Tracking Lambda (consume from SQS, write to DynamoDB) ────────
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

        # SQS → Lambda event source mapping
        size_tracking_fn.add_event_source(
            lambda_event_sources.SqsEventSource(size_tracking_queue, batch_size=10)
        )

        self.bucket.grant_read(size_tracking_fn)
        table.grant_write_data(size_tracking_fn)

        # ── Logging Lambda (consume from SQS, write to CloudWatch Logs) ──────
        logging_fn = lambda_.Function(
            self, "LoggingFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="logging_lambda.lambda_handler",
            code=lambda_.Code.from_asset("lambda/"),
            environment={
                "REGION":      self.region,
                "LOG_GROUP":   f"/aws/lambda/logging-{self.stack_name}",
            },
            timeout=Duration.seconds(30),
        )

        # SQS → Lambda event source mapping
        logging_fn.add_event_source(
            lambda_event_sources.SqsEventSource(logging_queue, batch_size=10)
        )

        # Create custom log group for logging lambda
        log_group = logs.LogGroup(
            self, "LoggingLogGroup",
            log_group_name=f"/aws/lambda/logging-{self.stack_name}",
            retention=logs.RetentionDays.ONE_DAY,
            removal_policy=RemovalPolicy.DESTROY,
        )

        logging_fn.add_environment("LOG_GROUP", log_group.log_group_name)
        log_group.grant_write(logging_fn)

        # ── CloudWatch Metric Filter ─────────────────────────────────────────
        # Extract size_delta from JSON logs: {"object_name": "...", "size_delta": N}
        metric_filter = logs.MetricFilter(
            self, "SizeMetricFilter",
            log_group=log_group,
            metric_namespace="Assignment4App",
            metric_name="TotalObjectSize",
            filter_pattern=logs.FilterPattern.literal('{ $.size_delta = * }'),
            metric_value="$.size_delta",
        )

        # ── CloudWatch Alarm ───────────────────────────────────────────────────
        # Trigger when cumulative SUM > 20 bytes
        alarm_metric = cw.Metric(
            namespace="Assignment4App",
            metric_name="TotalObjectSize",
            statistic="Sum",
            period=Duration.minutes(5),  # Adjust for testing
        )

        alarm = cw.Alarm(
            self, "TotalSizeAlarm",
            metric=alarm_metric,
            threshold=20,
            evaluation_periods=1,
            datapoints_to_alarm=1,
        )

        # ── Cleaner Lambda (delete largest object) ────────────────────────────
        cleaner_fn = lambda_.Function(
            self, "CleanerFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="cleaner_lambda.lambda_handler",
            code=lambda_.Code.from_asset("lambda/"),
            environment={
                "BUCKET_NAME": self.bucket.bucket_name,
                "REGION":      self.region,
            },
            timeout=Duration.seconds(30),
        )

        self.bucket.grant_read_write(cleaner_fn)

        # ── Plotting Lambda ────────────────────────────────────────────────────
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

        self.bucket.grant_read_write(plotting_fn)
        table.grant_read_data(plotting_fn)
        plotting_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:ListAllMyBuckets"],
                resources=["*"],
            )
        )

        fn_url = plotting_fn.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.NONE,
        )
        self.plotting_url: str = fn_url.url

        # ── Store references for DriverStack ───────────────────────────────────
        self.cleaner_fn = cleaner_fn
        self.alarm = alarm

        # ── Outputs ────────────────────────────────────────────────────────────
        CfnOutput(self, "BucketName",          value=self.bucket.bucket_name)
        CfnOutput(self, "SNSTopicArn",         value=sns_topic.topic_arn)
        CfnOutput(self, "LogGroupName",        value=log_group.log_group_name)
        CfnOutput(self, "PlottingFunctionUrl", value=fn_url.url)
