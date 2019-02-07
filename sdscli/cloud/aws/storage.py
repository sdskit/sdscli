

import os
import re
import json
import boto3
import hashlib
import base64
from pprint import pformat
from collections import OrderedDict
from operator import itemgetter
from fabric.api import execute, hide

from prompt_toolkit.shortcuts import prompt, print_tokens
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.validation import Validator, ValidationError
from pygments.token import Token

from sdscli.log_utils import logger
from sdscli.conf_utils import get_user_config_path, get_user_files_path, SettingsConf
from sdscli.os_utils import validate_dir
from sdscli.func_utils import get_func
from sdscli.prompt_utils import (YesNoValidator, SelectionValidator,
                                 MultipleSelectionValidator, Ec2InstanceTypeValidator, PriceValidator, highlight,
                                 print_component_header)
from .utils import *
from .asg import prompt_secgroup

from osaka.main import put


prompt_style = style_from_dict({
    Token.Alert: 'bg:#D8060C',
    Token.Username: '#D8060C',
    Token.Param: '#3CFF33',
})


@cloud_config_check
def ls(args, conf):
    """List all buckets."""

    for bucket in get_buckets():
        print(bucket['Name'])


def prompt_role(roles):
    """Prompt for role to use."""

    names = list(roles.keys())
    pt = [(Token, "Current roles are:\n\n")]
    for i, x in enumerate(names):
        pt.append((Token.Param, "{}".format(i)))
        pt.append((Token, ". {} - {} ({})\n".format(x,
                                                    roles[x]['Arn'], roles[x]['CreateDate'])))
    pt.append((Token, "\nSelect role to use for lambda execution: "))
    while True:
        sel = int(prompt(get_prompt_tokens=lambda x: pt, style=prompt_style,
                         validator=SelectionValidator()).strip())
        try:
            return names[sel]
        except IndexError:
            print("Invalid selection: {}".format(sel))


@cloud_config_check
def ship_style(args, conf):
    """Ship style to bucket."""

    # get bucket name
    bucket_name = conf.get(
        'DATASET_BUCKET') if args.bucket is None else args.bucket

    # get fab function
    func = get_func('sdscli.adapters.{}.fabfile'.format(
        args.type), args.subparser2)

    # execute
    execute(func, bucket_name, args.encrypt, roles=['mozart'])

    # turn on website hosting and set index and error docs
    bw_args = {
        'WebsiteConfiguration': {
            'ErrorDocument': {
                'Key': 'index.html'
            },
            'IndexDocument': {
                'Suffix': 'index.html'
            }
        }
    }
    configure_bucket_website(bucket_name, **bw_args)


@cloud_config_check
def create_staging_area(args, conf):
    """Provision staging area in bucket."""

    # get staging area conf
    sa_cfg = conf._cfg.get('STAGING_AREA', {})

    # create boto3 clients
    s3_res = boto3.resource('s3')
    sns_client = boto3.client('sns')

    # get bucket name
    bucket_name = conf.get(
        'DATASET_BUCKET') if args.bucket is None else args.bucket
    bucket = get_bucket(bucket_name, c=s3_res)
    logger.debug("bucket: {}".format(bucket))

    # create SNS topic
    logger.debug("prefix: {}".format(args.prefix))
    logger.debug("suffix: {}".format(args.suffix))
    shasum = hashlib.sha224(
        "{}-{}-{}".format(bucket_name, args.prefix, args.suffix)).hexdigest()
    topic_name = "{}-dataset-{}".format(conf.get('VENUE'), shasum[:4])
    logger.debug("topic_name: {}".format(topic_name))
    topic_arn = create_topic(Name=topic_name, c=sns_client)['TopicArn']
    logger.debug("topic_arn: {}".format(topic_arn))

    # add policy to allow S3 to publish to topic
    pol = {
        "Version": "2008-10-17",
        "Id": "__default_policy_ID",
        "Statement": [
            {
                "Sid": "__default_statement_ID",
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": [
                    "SNS:GetTopicAttributes",
                    "SNS:SetTopicAttributes",
                    "SNS:AddPermission",
                    "SNS:RemovePermission",
                    "SNS:DeleteTopic",
                    "SNS:Subscribe",
                    "SNS:ListSubscriptionsByTopic",
                    "SNS:Publish",
                    "SNS:Receive"
                ],
                "Resource": topic_arn,
                "Condition": {
                    "StringEquals": {
                        "aws:SourceArn": "arn:aws:s3:::{}".format(bucket_name)
                    }
                }
            }
        ]
    }
    sns_client.set_topic_attributes(TopicArn=topic_arn, AttributeName="Policy",
                                    AttributeValue=json.dumps(pol))
    sns_client.set_topic_attributes(TopicArn=topic_arn, AttributeName="DisplayName",
                                    AttributeValue=topic_name)

    # create notification event on bucket staging area
    notification_name = "data-staged-{}".format(topic_name)
    logger.debug("notification_name: {}".format(notification_name))
    bn_args = {
        'NotificationConfiguration': {
            'TopicConfigurations': [
                {
                    'Id': notification_name,
                    'TopicArn': topic_arn,
                    'Events': [
                        's3:ObjectCreated:*',
                    ],
                    'Filter': {
                        'Key': {
                            'FilterRules': [
                                {
                                    'Name': 'prefix',
                                    'Value': args.prefix,
                                },
                                {
                                    'Name': 'suffix',
                                    'Value': args.suffix,
                                },
                            ]
                        }
                    }
                }
            ]
        }
    }
    configure_bucket_notification(bucket_name, c=s3_res, **bn_args)

    # create lambda zip file and upload to code bucket
    zip_file = "/tmp/data-staged.zip"
    func = get_func('sdscli.adapters.{}.fabfile'.format(
        args.type), 'create_zip')
    if args.debug:
        execute(func, "mozart/ops/hysds-cloud-functions/aws/data-staged",
                zip_file, roles=['mozart'])
    else:
        with hide('everything'):
            execute(func, "mozart/ops/hysds-cloud-functions/aws/data-staged",
                    zip_file, roles=['mozart'])
    #code_bucket = "s3://{}/{}".format(conf.get('S3_ENDPOINT'), conf.get('CODE_BUCKET'))
    #zip_url = os.path.join(code_bucket, 'data-staged.zip')
    #put(zip_file, zip_url)

    # prompt for security groups
    cur_sgs = {i['GroupId']: i for i in get_sgs()}
    logger.debug("cur_sgs: {}".format(pformat(cur_sgs)))
    desc = "\nSelect security groups lambda will use (space between each selected): "
    if 'LAMBDA_SECURITY_GROUPS' in sa_cfg and 'LAMBDA_VPC' in sa_cfg:
        sgs = sa_cfg.get('LAMBDA_SECURITY_GROUPS', [])
        vpc_id = sa_cfg.get('LAMBDA_VPC', None)
    else:
        sgs, vpc_id = prompt_secgroup(cur_sgs, desc)
    logger.debug("security groups: {}".format(sgs))
    logger.debug("VPC ID: {}".format(vpc_id))

    # get current AZs
    cur_azs = {i['ZoneName']: i for i in get_azs()}
    logger.debug("cur_azs: {}".format(pformat(cur_azs)))

    # get subnet IDs and corresponding AZs for VPC
    subnets = []
    azs = set()
    for sn in get_subnets_by_vpc(vpc_id):
        sn_id = sn.subnet_id
        sn_az = sn.availability_zone
        if cur_azs[sn_az]['State'] == 'available':
            subnets.append(sn_id)
            azs.add(sn_az)
    azs = list(azs)
    logger.debug("subnets: {}".format(pformat(subnets)))
    logger.debug("azs: {}".format(pformat(azs)))

    # prompt for role
    roles = get_roles()
    logger.debug("Found {} roles.".format(len(roles)))
    cur_roles = OrderedDict([(i['Arn'], i) for i in sorted(roles,
                                                           key=itemgetter('CreateDate'))])
    if 'LAMBDA_ROLE' in sa_cfg:
        role = sa_cfg['LAMBDA_ROLE']
    else:
        role = prompt_role(cur_roles)
    logger.debug("Selected role: {}".format(role))

    # prompt for job type, release, and queue
    if 'JOB_TYPE' in sa_cfg:
        job_type = sa_cfg['JOB_TYPE']
    else:
        job_type = prompt(get_prompt_tokens=lambda x:
                          [(Token, "Enter job type to submit on data staged event: ")],
                          style=prompt_style).strip()
    logger.debug("job type: {}".format(job_type))
    if 'JOB_RELEASE' in sa_cfg:
        job_release = sa_cfg['JOB_RELEASE']
    else:
        job_release = prompt(get_prompt_tokens=lambda x:
                             [(Token, "Enter release version for {}: ".format(job_type))],
                             style=prompt_style).strip()
    logger.debug("job release: {}".format(job_release))
    if 'JOB_QUEUE' in sa_cfg:
        job_queue = sa_cfg['JOB_QUEUE']
    else:
        job_queue = prompt(get_prompt_tokens=lambda x:
                           [(Token, "Enter queue name to submit {}-{} jobs to: ".format(job_type, job_release))],
                           style=prompt_style).strip()
    logger.debug("job queue: {}".format(job_queue))

    # create lambda
    function_name = "{}-dataset-{}-submit_ingest".format(conf.get('VENUE'),
                                                         args.prefix.replace('/', ''))
    lambda_client = boto3.client('lambda')
    cf_args = {
        "FunctionName": function_name,
        "Runtime": "python2.7",
        "Role": role,
        "Handler": "lambda_function.lambda_handler",
        "Code": {
            "ZipFile": open(zip_file, 'rb').read(),
            # "S3Bucket": conf.get('CODE_BUCKET'),
            # "S3Key": os.path.basename(zip_url)
        },
        "Description": "Lambda function to submit ingest job for data staged to S3 staging area.",
        "VpcConfig": {
            "SubnetIds": subnets,
            "SecurityGroupIds": sgs,
        },
        "Environment": {
            "Variables": {
                "DATASET_S3_ENDPOINT": conf.get('DATASET_S3_ENDPOINT'),
                "JOB_TYPE": job_type,
                "JOB_RELEASE": job_release,
                "JOB_QUEUE": job_queue,
                "MOZART_URL": "https://{}/mozart".format(conf.get('MOZART_PVT_IP'))
            }
        }
    }
    lambda_resp = lambda_client.create_function(**cf_args)
    logger.debug("lambda_resp: {}".format(lambda_resp))

    # add permission for sns to invoke lambda function
    lambda_client.add_permission(Action="lambda:InvokeFunction", FunctionName=function_name,
                                 Principal="sns.amazonaws.com", StatementId="ID-1",
                                 SourceArn=topic_arn)

    # subscribe lambda endpoint to sns
    sns_resp = sns_client.subscribe(TopicArn=topic_arn, Protocol="lambda",
                                    Endpoint=lambda_resp['FunctionArn'])
    logger.debug("sns_resp: {}".format(sns_resp))
