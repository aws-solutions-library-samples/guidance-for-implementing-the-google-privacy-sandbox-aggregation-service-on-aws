from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_elasticloadbalancingv2 as elbv2,
    aws_autoscaling as autoscaling,
    Duration,
    Aws,
    aws_ec2 as ec2,
    aws_wafv2 as wafv2,
)


from constructs import Construct

class CollectorServiceStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        source_kinesis_stream,
        kms_key,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.collector_ecr_repo_name = self.node.try_get_context("collector_ecr_repo_name")

        vpc = ec2.Vpc(self, "papi-demo-vpc")

        cluster = ecs.Cluster(self, "papi-ecs", vpc=vpc, container_insights=True)

        ecs_ami = ecs.EcsOptimizedImage.amazon_linux2(ecs.AmiHardwareType.ARM)

        cluster.add_capacity("DefaultAutoScalingGroup",
                             instance_type=ec2.InstanceType("t4g.medium"),
                             machine_image=ecs_ami,
                             block_devices=[autoscaling.BlockDevice(
                                 device_name="/dev/xvda",
                                 volume=autoscaling.BlockDeviceVolume.ebs(volume_size=30, encrypted=True)
                             )]
        )

        container_uri = ssm.StringParameter.value_for_string_parameter(self ,"collector-api-container-uri")
    
        task_definition = ecs.Ec2TaskDefinition(self, "collector-api-td")
        container = task_definition.add_container("collector-api",
                                                  image=ecs.ContainerImage.from_registry(container_uri),
                                                  memory_limit_mib=512,
                                                  cpu=256,
                                                  logging=ecs.LogDrivers.aws_logs(stream_prefix="collector-api"))
        container.add_port_mappings(ecs.PortMapping(container_port=8080))
        task_definition.add_to_task_role_policy(iam.PolicyStatement(
            actions=["kinesis:PutRecord", "kinesis:PutRecords", "kinesis:ListShards"],
            resources=[f"arn:aws:kinesis:{Aws.REGION}:{Aws.ACCOUNT_ID}:stream/{source_kinesis_stream}"]
        ))
        task_definition.add_to_task_role_policy(iam.PolicyStatement(
            actions=["kms:GenerateDataKey"],
            resources=[f"arn:aws:kms:{Aws.REGION}:{Aws.ACCOUNT_ID}:key/{kms_key}"]
        ))     
        task_definition.add_to_task_role_policy(iam.PolicyStatement(
            actions=["sts:GetCallerIdentity"],
            resources=["*"]
        ))
        task_definition.add_to_task_role_policy(iam.PolicyStatement(
            actions=["cloudwatch:PutMetricData"],
            resources=["*"]
        ))
        task_definition.add_to_execution_role_policy(iam.PolicyStatement(
            actions=["ecr:BatchCheckLayerAvailability",
                     "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage"],
            resources=[f"arn:aws:ecr:{Aws.REGION}:{Aws.ACCOUNT_ID}:repository/{self.collector_ecr_repo_name}"]
        ))
        task_definition.add_to_execution_role_policy(iam.PolicyStatement(
            actions=["ecr:GetAuthorizationToken"],
            resources=["*"]
        ))
    
    
        
        service = ecs.Ec2Service(self, "collector-api-ecs-svc",
                                 cluster=cluster,
                                 task_definition=task_definition)

        lb = elbv2.ApplicationLoadBalancer(self, "LB",
                                           vpc=vpc,
                                           internet_facing=True)
        

        health_check = elbv2.HealthCheck(
            interval=Duration.seconds(60),
            path="/actuator/health",
            timeout=Duration.seconds(5)
        )
        
        listener = lb.add_listener("Listener", port=80)
        listener.add_targets("ECS",
                             port=80,
                             health_check=health_check,
                             targets=[service.load_balancer_target(
                                 container_name="collector-api",
                                 container_port=8080
                                 )])
        
        
        managed_rules = [{
            "name"            : "AWSManagedRulesCommonRuleSet",
            "priority"        : 10,
            "override_action" : "none",
            "excluded_rules"  : [],
        },{
            "name"            : "AWSManagedRulesAmazonIpReputationList",
            "priority"        : 20,
            "override_action" : "none",
            "excluded_rules"  : [],
        },{
            "name"            : "AWSManagedRulesKnownBadInputsRuleSet",
            "priority"        : 30,
            "override_action" : "none",
            "excluded_rules"  : [],
        },{
            "name"            : "AWSManagedRulesSQLiRuleSet",
            "priority"        : 40,
            "override_action" : "none",
            "excluded_rules"  : [],
        },{
            "name"            : "AWSManagedRulesLinuxRuleSet",
            "priority"        : 50,
            "override_action" : "none",
            "excluded_rules"  : [],
        },{
            "name"            : "AWSManagedRulesUnixRuleSet",
            "priority"        : 60,
            "override_action" : "none",
            "excluded_rules"  : [],
        }]
        
        wafacl = wafv2.CfnWebACL(self, id="WAF",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow=wafv2.CfnWebACL.AllowActionProperty(), block=None),
            scope="REGIONAL",
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
            cloud_watch_metrics_enabled=True,
            metric_name                ="waf-regional",
            sampled_requests_enabled   =True
            ),
            description = "WAFv2 ACL for Regional",
            name        = "waf-regional",
            rules       = self.make_rules(managed_rules),
        )
    
        wafv2.CfnWebACLAssociation(self, 'collectionwafassociation',
                               resource_arn=lb.load_balancer_arn,
                               web_acl_arn=wafacl.attr_arn)
        
    def make_rules(self, list_of_rules={}):
        rules = list()
        for r in list_of_rules:
            rule = wafv2.CfnWebACL.RuleProperty(
            name             = r["name"],
            priority         = r["priority"],
            override_action  = wafv2.CfnWebACL.OverrideActionProperty(none={}),
            statement        = wafv2.CfnWebACL.StatementProperty(
                managed_rule_group_statement = wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                name           = r["name"],
                vendor_name    = "AWS",
                excluded_rules = []
                )
            ),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled = True,
                metric_name                 = r["name"],
                sampled_requests_enabled    = True
            )
            )
            rules.append(rule)

        ruleGeoMatch = wafv2.CfnWebACL.RuleProperty(
            name     = 'GeoMatch',
            priority =  0,
            action   = wafv2.CfnWebACL.RuleActionProperty(
            block={} ## To disable, change to *count*
            ),
            statement = wafv2.CfnWebACL.StatementProperty(
            not_statement = wafv2.CfnWebACL.NotStatementProperty(
                statement = wafv2.CfnWebACL.StatementProperty(
                geo_match_statement = wafv2.CfnWebACL.GeoMatchStatementProperty(

                    country_codes = [
                    "VE", 
                    ]
                ) 
                ) 
            ) 
            ), 
            visibility_config = wafv2.CfnWebACL.VisibilityConfigProperty(
            cloud_watch_metrics_enabled = True,
            metric_name                 = 'GeoMatch',
            sampled_requests_enabled    = True
            ) 
        ) 
        rules.append(ruleGeoMatch)


        ruleLimitRequests100 = wafv2.CfnWebACL.RuleProperty(
                name     = 'LimitRequests100',
                priority = 1,
                action   = wafv2.CfnWebACL.RuleActionProperty(
                block = {}
                ), 
                statement= wafv2.CfnWebACL.StatementProperty(
                rate_based_statement = wafv2.CfnWebACL.RateBasedStatementProperty(
                    limit              = 100,
                    aggregate_key_type = "IP"
                ) 
                ), 
                visibility_config= wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled = True,
                metric_name                 = 'LimitRequests100',
                sampled_requests_enabled    = True
                )
            ) 
        rules.append(ruleLimitRequests100);

        return rules