import aws_cdk as cdk

from aws_cdk import Stack, aws_iam as iam, aws_s3 as s3, aws_ecr as ecr, aws_codecommit as codecommit, aws_ssm as ssm

from aws_cdk import aws_codebuild as codebuild

from constructs import Construct


class CollectorBuild(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.collector_ecr_repo_name = self.node.try_get_context("collector_ecr_repo_name")

        code_repo = codecommit.Repository(
          self,
          "collector-api-cc",
          repository_name="collector-api",
          code=codecommit.Code.from_directory("source/collector-api/", "develop")
        )
        
        self.container_repository = ecr.Repository(
          self,
          "collector_ecr_repo_name",
          removal_policy=cdk.RemovalPolicy.DESTROY,
          image_scan_on_push=True,
          repository_name=self.collector_ecr_repo_name
        )
        
        collector_container_uri = ssm.StringParameter(
          self, "CollectorAPISSMParam",
          parameter_name="collector-api-container-uri",
          string_value="empty"
        )

        build_project = codebuild.Project(
            self,
            "collectorbuild",
            source=codebuild.Source.code_commit(
                identifier="collectorapi",
                repository=code_repo
              ),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_ARM,
                privileged=True
            ),
            environment_variables={
                'REPO_ECR': codebuild.BuildEnvironmentVariable(
                    value=self.container_repository.repository_uri),
                'AWS_ACCOUNT_ID': codebuild.BuildEnvironmentVariable(
                    value=self.account)
            },
            build_spec=codebuild.BuildSpec.from_source_filename(
                "buildspec.yml"
            ),
        )
        collector_container_uri.grant_write(build_project)
        self.container_repository.grant_pull_push(build_project)
        