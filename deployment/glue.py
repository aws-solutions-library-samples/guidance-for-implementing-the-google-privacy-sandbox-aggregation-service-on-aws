import json
from constructs import Construct
from aws_cdk import (
    App, 
    Stack,
    CfnOutput,
    Tags,
    aws_iam as iam,
    aws_s3 as s3,
    RemovalPolicy,
    aws_glue as glue,
    aws_kms as kms,
    aws_s3_deployment as s3_deploy
)
import aws_cdk.aws_glue_alpha as glue_alpha

import aws_cdk.aws_glue_alpha as glue_alpha

from aws_cdk.aws_stepfunctions import (
    JsonPath
)

class GlueStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, kms_key,api_name: str,source_kinesis_stream,
                 s3_collector_destination, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
      
        self.raw_job_script = self.node.try_get_context("raw_job_script")
        self.avro_job_script = self.node.try_get_context("avro_job_script")
        self.glue_database_name = self.node.try_get_context("glue_database_name")
        self.glue_table_agg_raw = self.node.try_get_context("glue_table_agg_raw")
        self.glue_table_agg_avro = self.node.try_get_context("glue_table_agg_avro")
        self.aggregate_raw_job_name = self.node.try_get_context("aggregate_raw_job_name")
        self.aggregate_avro_job_name = self.node.try_get_context("aggregate_avro_job_name")
        self.window_size= self.node.try_get_context("stream_batch_window_size") or "100 seconds"
        self.classification = self.node.try_get_context("classification")
        self.s3_collector_destination = s3_collector_destination
        
        self.add_buckets()
        self.add_role(kms_key,source_kinesis_stream)
        self.add_scripts()
        self.add_database(self.glue_database_name)

        #  raw data
        self.add_jobs(source_kinesis_stream,self.window_size,self.aggregate_raw_job_name,self.raw_job_script,self.glue_database_name,self.glue_table_agg_raw,kms_key)
        self.add_crawler(self.aggregate_raw_job_name,self.glue_database_name,self.glue_table_agg_raw,data_type="raw")

        #  avro data
        self.add_jobs(source_kinesis_stream,self.window_size,self.aggregate_avro_job_name,self.avro_job_script,self.glue_database_name,self.glue_table_agg_avro,kms_key)
        self.add_crawler(self.aggregate_avro_job_name,self.glue_database_name,self.glue_table_agg_avro,data_type="avro")

  ##############################################################################
  # S3 Buckets
  ##############################################################################

    def add_buckets(self):
        
        self.glue_asset_bucket = s3.Bucket(
            self,
            "glue_asset_bucket",
            bucket_name=f"aws-glue-assets-logs-{self.account}-{self.region}",
            encryption=s3.BucketEncryption.KMS_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )
        CfnOutput(self, "glue-asset-bucket-name", value=self.glue_asset_bucket.bucket_name)   
        Tags.of(self.glue_asset_bucket).add("Classification", self.classification)   

    ##############################################################################
    # GlueJob
    ##############################################################################

    def add_jobs(self,kinesis_stream,window_size,job_name,job_script,database_name,table_name,kms_key):
        
        kms_key.grant_encrypt_decrypt(self.role)
        self.service_cloudwatch = iam.ServicePrincipal(service='logs.amazonaws.com')
        kms_key.grant_encrypt_decrypt(self.service_cloudwatch)
        
        # Create Security configuration for the job
        self.glue_security_configuration = glue_alpha.SecurityConfiguration(
            self,
            f"{job_name}-security-configuration",
            security_configuration_name=f"{job_name}-security-configuration",
            s3_encryption={"mode": glue_alpha.S3EncryptionMode.S3_MANAGED},
            job_bookmarks_encryption=glue_alpha.JobBookmarksEncryption(
                mode=glue_alpha.JobBookmarksEncryptionMode.CLIENT_SIDE_KMS,
                kms_key=kms_key
            ),
            cloud_watch_encryption=glue_alpha.CloudWatchEncryption(
                mode=glue_alpha.CloudWatchEncryptionMode.KMS,
                kms_key=kms_key
            )       
        )

        arguments = {
            "--class":	"GlueApp",
            "--job-language":	"python",
            "--TempDir":	f"s3://{self.glue_asset_bucket.bucket_name}/temporary/",
            "--enable-metrics":	"true",
            "--enable-continuous-cloudwatch-log":	"true",
            "--enable-spark-ui":	"true",
            "--enable-auto-scaling":	"true",
            "--spark-event-logs-path":	f"s3://{self.glue_asset_bucket.bucket_name}/sparkHistoryLogs/",
            "--enable-glue-datacatalog":	"true",
            "--enable-job-insights":	"true",
            "--table":	table_name,
            "--databucket": self.s3_collector_destination.bucket_name,
            "--gluedatabasename": database_name,
            "--gluetablename": table_name,
            "--kds_stream_arn": kinesis_stream.stream_arn,
            "--kds_stream_name": kinesis_stream.stream_name,
            "--windowSize": window_size
        }

        self.glue_job = glue_alpha.Job(self, f"{job_name}-id",
            executable=glue_alpha.JobExecutable.python_streaming(
                glue_version=glue_alpha.GlueVersion.V4_0,
                python_version=glue_alpha.PythonVersion.THREE,
                script=glue_alpha.Code.from_bucket(self.glue_asset_bucket, "glue-scripts/" + job_script)
            ),
            job_name=job_name,
            role=self.role,
            default_arguments=arguments,
            security_configuration=self.glue_security_configuration,
            description=f"Aggregation Server job-{job_name}"
        )
  
    ##############################################################################
    # GlueJob script
    ##############################################################################

    def add_scripts(self):
        s3_deploy.BucketDeployment(
            self,
            "script-deployment",
            sources=[s3_deploy.Source.asset("./source/glue_scripts")],
            destination_bucket=self.glue_asset_bucket,
            destination_key_prefix="glue-scripts",
        )

    ##############################################################################
    # GlueJob roles
    ##############################################################################

    def add_role(self,kms_key,kinesis_stream):
        self.role = iam.Role(
            self,
            f"bigquery-glue-job-role",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
        )

        self.role.attach_inline_policy(
            iam.Policy(
                self,
                "glue_role_policy",
                statements=[
                    iam.PolicyStatement(
                        actions=[
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents",
                            "logs:AssociateKmsKey"
                        ],
                        resources=[
                            f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws-glue/jobs/*"
                        ],
                    ),
                    iam.PolicyStatement(
                        actions=[
                            "kinesis:DescribeStream",
                            "kinesis:GetRecords",
                            "kinesis:GetShardIterator",
                            "kinesis:ListShards",
                            "kinesis:DescribeLimits",
                        ],
                        resources=[
                            f"arn:aws:kinesis:{self.region}:{self.account}:stream/{kinesis_stream.stream_name}"
                        ],
                    ),
                    iam.PolicyStatement(
                        actions=[
                            "s3:GetBucketLocation",
                            "s3:ListBucket",
                            "s3:GetBucketAcl",
                            "s3:GetObject",
                            "s3:PutObject",
                            "s3:DeleteObject",
                        ],
                        resources=[self.s3_collector_destination.bucket_arn + "*", self.glue_asset_bucket.bucket_arn + "*"]
                    ),
                    iam.PolicyStatement(
                        actions=[
                            "kms:Decrypt"
                        ],
                        resources=[kms_key.key_arn],
                    )
                ],
            )
        )


        self.role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole"))



    def add_database(self,database_name):
        # create Database
        self.glue_database= glue_alpha.Database(
            self,
            id=self.glue_database_name,
            database_name=database_name
        )
        # Delete the database when deleting
        self.glue_database.apply_removal_policy(policy=RemovalPolicy.DESTROY)


    ##############################################################################
    # GlueCrawler
    ##############################################################################

    def add_crawler(self,job_name,database_name,table_name,data_type):

        # Create Glue crawler's IAM role
        self.glue_crawler_role = iam.Role(
            self, f'GlueCrawlerRole-{job_name}',
            assumed_by=iam.ServicePrincipal(
                'glue.amazonaws.com'),
        )
        self.glue_crawler_role.attach_inline_policy(
            iam.Policy(
                self,
                f"glue_crawler_role_policy-{job_name}",
                statements=[
                    iam.PolicyStatement(
                        actions=[
                            "s3:GetBucketLocation",
                            "s3:ListBucket",
                            "s3:GetBucketAcl",
                            "s3:GetObject",
                        ],
                        resources=[f"{self.s3_collector_destination.bucket_arn}/{table_name}/*"]
                    )
                ]
            )
        )

        # Add managed policies to Glue crawler role
        self.glue_crawler_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSGlueServiceRole'))

        
        self.audit_policy = glue.CfnCrawler.SchemaChangePolicyProperty(update_behavior='UPDATE_IN_DATABASE', delete_behavior='LOG')
        
        self.glue_crawler = glue.CfnCrawler(self,f"{job_name}-crawler",
            name= f"{job_name}-crawler",
            role=self.glue_crawler_role.role_arn,
            database_name=database_name,
            targets=glue.CfnCrawler.TargetsProperty(
                s3_targets= [glue.CfnCrawler.S3TargetProperty(
                    path=f"s3://{self.s3_collector_destination.bucket_name}/aggregation_report_{data_type}/",
                    exclusions= ["glue-scripts/**"],
                    sample_size=100
                )]
            ),
            schema_change_policy=self.audit_policy,
            configuration='{"Version":1.0,"CrawlerOutput":{"Partitions":{"AddOrUpdateBehavior":"InheritFromTable"}}}',
            recrawl_policy=glue.CfnCrawler.RecrawlPolicyProperty(
                recrawl_behavior='CRAWL_EVERYTHING'
            )
        )