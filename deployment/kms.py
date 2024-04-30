from aws_cdk import (
  Stack,
  aws_kms as kms,
)
from constructs import Construct

class KMSKeyStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)


    self.kms_key = kms.Key(self, "AggregationServerKey",
        enable_key_rotation=True,
        alias="aggregration_server_key"
        )