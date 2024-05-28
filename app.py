import aws_cdk as cdk
from aws_cdk import Tags

from deployment.collector_build import CollectorBuild
from deployment.collector_service import CollectorServiceStack
from deployment.kms import KMSKeyStack
from deployment.kds import KinesisDataStreamsStack
from deployment.s3 import S3Stack
from deployment.glue import GlueStack

from cdk_nag import AwsSolutionsChecks, NagSuppressions

app = cdk.App()
project_name = app.node.try_get_context("project_name")
guidance_description = "Guidance for deploying Privacy Sandbox Private Aggregation API on AWS (SO9455)"
collector_build = CollectorBuild(app, "CollectorBuild", description="guidance_description")
Tags.of(collector_build).add("project", project_name)

kms_key_stack = KMSKeyStack(app, "KMSKeyStack", description="guidance_description")
Tags.of(kms_key_stack).add("project", project_name)

s3_collector_destination = S3Stack(app, 'CollectedDataS3Stack', description="guidance_description")
Tags.of(s3_collector_destination).add("project", project_name)

s3_summary_destination = S3Stack(app, 'AggregationSummaryDataS3Stack', description="guidance_description")
Tags.of(s3_summary_destination).add("project", project_name)

kds_stack_aggregatable_report = KinesisDataStreamsStack(app, 'AggregatableGPSAggServiceCollectorKinesisDataStreamsStack',kms_key=kms_key_stack.kms_key,api_name="gps_aggregatable_report", description="guidance_description")
Tags.of(kds_stack_aggregatable_report).add("project", project_name)

glue_aggregatable_report = GlueStack(app, "GlueToS3Stack",kms_key=kms_key_stack.kms_key,api_name="gps_aggregatable_report",
  source_kinesis_stream=kds_stack_aggregatable_report.kinesis_stream,s3_collector_destination=s3_collector_destination.s3_bucket
, description="guidance_description")
Tags.of(glue_aggregatable_report).add("project", project_name)

collector_service = CollectorServiceStack(app, "CollectorService", source_kinesis_stream=kds_stack_aggregatable_report.kinesis_stream.stream_name, kms_key=kms_key_stack.kms_key.key_id, description="guidance_description")
collector_service.add_dependency(kms_key_stack)
collector_service.add_dependency(glue_aggregatable_report)
collector_service.add_dependency(kds_stack_aggregatable_report)
collector_service.add_dependency(s3_summary_destination)
collector_service.add_dependency(s3_collector_destination)

Tags.of(collector_service).add("project", project_name)

NagSuppressions.add_stack_suppressions(
    collector_build,
    [
        {
            "id": "AwsSolutions-S1",
            "reason": "S3 Access Logs are disabled for demo purposes.",
        },
        {
            "id": "AwsSolutions-IAM5",
            "reason": "AWS managed policies are allowed which sometimes uses * in the resources like - AWSGlueServiceRole has aws-glue-* . AWS Managed IAM policies have been allowed to maintain secured access with the ease of operational maintenance - however for more granular control the custom IAM policies can be used instead of AWS managed policies",
        },
        {
            "id": "AwsSolutions-CB4",
            "reason": "TODO: Decide if codebuild should be used"
        }
        
    ],
    apply_to_nested_stacks=True
)

NagSuppressions.add_stack_suppressions(
    glue_aggregatable_report,
    [
        {
            "id": "AwsSolutions-S1",
            "reason": "S3 Access Logs are disabled for demo purposes.",
        }
    ]
)


#CDK Nag Suppressions for s3
NagSuppressions.add_stack_suppressions(
    s3_summary_destination,
    [
        {
            "id": "AwsSolutions-S1",
            "reason": "S3 Access Logs are disabled for demo purposes.",
        }
    ]
)

#CDK Nag Suppressions for s3
NagSuppressions.add_stack_suppressions(
    s3_collector_destination,
    [
        {
            "id": "AwsSolutions-S1",
            "reason": "S3 Access Logs are disabled for demo purposes.",
        }
    ]
)

#CDK Nag Suppressions for kds
NagSuppressions.add_stack_suppressions(
    kds_stack_aggregatable_report,
    [
        {
            "id": "AwsSolutions-KDS3",
            "reason": "Using custom KMS key",
        }
    ]
)


NagSuppressions.add_stack_suppressions(
    glue_aggregatable_report,
    [
        {
            "id": "AwsSolutions-IAM5",
            "reason": "S3Bucket Deployment contains a wildcard permissions have apply to bucket",
        },
        {
            "id": "AwsSolutions-IAM4",
            "reason": "AWS Managed IAM policies are used for AWSGlueServiceRole and AmazonEC2ContainerRegistryReadOnly been allowed to maintain secured access with the ease of operational maintenance - however for more granular control the custom IAM policies can be used instead of AWS managed policies",
        },
        {
            "id": "AwsSolutions-S1",
            "reason": "S3 Access Logs are disabled for demo purposes.",
        },
        {
            "id": "AwsSolutions-GL1",
            "reason": "Crawler lambda version not configurable",
        },
        {
            "id": "AwsSolutions-L1",
            "reason": "Bucket Deployment lambda version not configurable",
        }
    ]
)

#CDK Nag Suppressions for collector service
NagSuppressions.add_stack_suppressions(
    collector_service,
    [
        {
            "id": "AwsSolutions-EC23",
            "reason": "Load balancer must accept traffic from internet, using WAF in front of for security.",
        },
        {
            "id": "AwsSolutions-ELB2",
            "reason": "ELB access logs are disabled for demo purposes only.",
        },
        {
            "id": "AwsSolutions-AS3",
            "reason": "Default behaviour of ECS construct"
        },
        {
            "id": "AwsSolutions-SNS3",
            "reason": "Default behaviour of ECS construct"
        },
        {
            "id": "AwsSolutions-SNS2",
            "reason": "Default behaviour of ECS construct"
        },
        {
            "id": "AwsSolutions-L1",
            "reason": "Default behaviour of ECS construct"
        },
        {
            "id": "AwsSolutions-IAM5",
            "reason": "Default behaviour of ECS construct"
        },
        {
            "id": "AwsSolutions-IAM4",
            "reason": "Default behaviour of ECS construct"
        },
        {
            "id": "AwsSolutions-VPC7",
            "reason": "VPC Flow Logs not enabled for demo."
        }
    ]
)


cdk.Aspects.of(app).add(AwsSolutionsChecks())

app.synth()
