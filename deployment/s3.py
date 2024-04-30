import aws_cdk as cdk
from aws_cdk import (
  Stack,
  aws_s3 as s3,  
)
from constructs import Construct

class S3Stack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)
    
    
    # get context s3 data classification tag
    self.classification = self.node.try_get_context("classification")

    self.s3_bucket = s3.Bucket(self, "s3bucket",
      block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
      removal_policy=cdk.RemovalPolicy.DESTROY,
      auto_delete_objects=True,
      enforce_ssl=True)


    # associating a Classification tag
    cdk.Tags.of(self.s3_bucket).add("Classification", self.classification)  
    
    cdk.CfnOutput(self, 'S3Bucket',
      value=self.s3_bucket.bucket_name,
      export_name=f'{self.stack_name}-S3Bucket')