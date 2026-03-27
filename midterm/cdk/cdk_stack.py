from aws_cdk import Stack
from constructs import Construct


class CdkStack(Stack):
    """Minimal base stack kept for consistency with prior assignments."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
