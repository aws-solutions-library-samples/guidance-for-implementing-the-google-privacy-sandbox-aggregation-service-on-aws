import random
import string
import aws_cdk as cdk
from aws_cdk import (
  Stack,NestedStack,
  aws_kinesis,RemovalPolicy
)
from constructs import Construct


class KinesisDataStreamsStack(NestedStack):

  def __init__(self, scope: Construct, construct_id: str,kms_key,api_name: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)
    
    # Retrieving kds_retention_hours from the context.json
    self.kds_retention_hours = self.node.try_get_context("kds_retention_hours") or 24
    
    KINESIS_STREAM_NAME = cdk.CfnParameter(self, 'KinesisStreamName',
      type='String',
      description=f'{api_name} data stream name',
      default=f'{api_name}'
    )   

    self.kinesis_stream = aws_kinesis.Stream(self, "SourceKinesisStreams",
      retention_period=cdk.Duration.hours(int(self.kds_retention_hours)),
      removal_policy = RemovalPolicy.DESTROY,
      encryption = aws_kinesis.StreamEncryption.KMS,
      encryption_key=kms_key,
      stream_mode=aws_kinesis.StreamMode.ON_DEMAND,
      stream_name=KINESIS_STREAM_NAME.value_as_string)

    
    cdk.CfnOutput(self, 'KinesisDataStreamsName',
      value=self.kinesis_stream.stream_name,
      export_name=f'{self.stack_name}-KinesisDataStreamsName')