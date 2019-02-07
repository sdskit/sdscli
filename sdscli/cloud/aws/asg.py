


import os, re, json, boto3
from pprint import pformat
from collections import OrderedDict
from operator import itemgetter

from prompt_toolkit.shortcuts import prompt, print_tokens
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.validation import Validator, ValidationError
from pygments.token import Token

from sdscli.log_utils import logger
from sdscli.conf_utils import get_user_config_path, get_user_files_path, SettingsConf
from sdscli.os_utils import validate_dir
from sdscli.prompt_utils import (YesNoValidator, SelectionValidator,
MultipleSelectionValidator, Ec2InstanceTypeValidator, PriceValidator, highlight,
print_component_header)
from .utils import *


prompt_style = style_from_dict({
    Token.Alert: 'bg:#D8060C',
    Token.Username: '#D8060C',
    Token.Param: '#3CFF33',
})


@cloud_config_check
def ls(args, conf):
    """List all Autoscaling groups."""

    for asg in get_asgs(): print(asg['AutoScalingGroupName'])


def prompt_image(images):
    """Prompt for image to use."""

    ids = list(images.keys())
    pt = [(Token, "Current verdi AMIs are:\n\n")]
    for i, x in enumerate(ids):
        pt.append((Token.Param, "{}".format(i)))
        pt.append((Token, ". {} - {} ({})\n".format(images[x]['Name'], x, images[x]['CreationDate'])))
    pt.append((Token, "\nSelect verdi AMI to use for launch configurations: "))
    while True:
        sel = int(prompt(get_prompt_tokens=lambda x: pt, style=prompt_style,
                         validator=SelectionValidator()).strip())
        try: return ids[sel]
        except IndexError:
            print("Invalid selection: {}".format(sel))


def prompt_keypair(keypairs):
    """Prompt for key pair to use."""

    ids = list(keypairs.keys())
    pt = [(Token, "Current key pairs are:\n\n")]
    for i, x in enumerate(ids):
        pt.append((Token.Param, "{}".format(i)))
        pt.append((Token, ". {}\n".format(x)))
    pt.append((Token, "\nSelect key pair to use for launch configurations: "))
    while True:
        sel = int(prompt(get_prompt_tokens=lambda x: pt, style=prompt_style,
                         validator=SelectionValidator()).strip())
        try: return ids[sel]
        except IndexError:
            print("Invalid selection: {}".format(sel))

def prompt_roles(roles):
    """Prompt for role to use."""

    ids = list(roles.keys())
    pt = [(Token, "Current roles are:\n\n")]
    for i, x in enumerate(ids):
        pt.append((Token.Param, "{}".format(i)))
        pt.append((Token, ". {}\n".format(x)))
    pt.append((Token, "\nSelect role to use for launch configurations: "))
    while True:
        sel = int(prompt(get_prompt_tokens=lambda x: pt, style=prompt_style,
                         validator=SelectionValidator()).strip())
        try: return ids[sel]
        except IndexError:
            print("Invalid selection: {}".format(sel))

def prompt_secgroup(sgs, desc=None):
    """Prompt for security groups to use."""

    if desc is None:
        desc = "\nSelect security groups to use for launch configurations (space between each selected): "
    ids = list(sgs.keys())
    pt = [(Token, "Current security groups are:\n\n")]
    for i, x in enumerate(ids):
        pt.append((Token.Param, "{}".format(i)))
        pt.append((Token, ". {} - {} - {}\n".format(sgs[x]['VpcId'], sgs[x]['GroupName'], x)))
    pt.append((Token, desc))
    while True:
        sels = list(map(int, [i.strip() for i in prompt(get_prompt_tokens=lambda x: pt, style=prompt_style,
                                                   validator=MultipleSelectionValidator()).split()]))
        sgs_ids = set()
        vpc_ids = set()
        invalid = False
        for sel in sels:
            try:
                sgs_ids.add(ids[sel])
                vpc_ids.add(sgs[ids[sel]]['VpcId'])
            except IndexError:
                print("Invalid selection: {}".format(sel))
                invalid = True
                break
        if invalid: continue
        if len(vpc_ids) > 1:
            print("Invalid selections. Security groups from multiple VPC IDs selected: {}".format(list(vpc_ids)))
            continue
        return list(sgs_ids), list(vpc_ids)[0]


@cloud_config_check
def create(args, conf):
    """Create Autoscaling group."""

    # get autoscaling conf
    asg_cfg = conf._cfg.get('ASG', {})

    # get clients
    c = boto3.client('autoscaling')
    ec2 = boto3.client('ec2')

    # get current autoscaling groups
    cur_asgs = { i['AutoScalingGroupName']: i for i in get_asgs(c) }
    logger.debug("cur_asgs: {}".format(pformat(cur_asgs)))

    # get current launch configs
    cur_lcs = { i['LaunchConfigurationName']: i for i in get_lcs(c) }
    logger.debug("cur_lcs: {}".format(pformat(cur_lcs)))

    
    # get current key pairs
    cur_keypairs = { i['KeyName']: i for i in get_keypairs(ec2) }
    logger.debug("cur_keypairs: {}".format(pformat(cur_keypairs)))
   

    # get roles
    cur_roles = { i['RoleName']: i for i in get_roles() }
    logger.debug("cur_roles: {}".format(pformat(cur_roles)))

    # get current AMIs
    verdi_re = re.compile(r'(?:verdi|autoscale)', re.IGNORECASE)
    cur_images = OrderedDict([(i['ImageId'], i) for i in 
                               [x for x in sorted(get_images(c=ec2, Filters=[{'Name':'is-public','Values':['false']}]), 
                                             key=itemgetter('CreationDate')) if verdi_re.search(x['Name'])]
                             ])
    logger.debug("cur_images: {}".format(json.dumps(cur_images, indent=2)))
    logger.debug("cur_images.keys(): {}".format(list(cur_images.keys())))

    # get current security groups
    cur_sgs = { i['GroupId']: i for i in get_sgs(ec2) }
    logger.debug("cur_sgs: {}".format(pformat(cur_sgs)))

    # prompt for verdi AMI
    if 'AMI' in asg_cfg:
        ami = asg_cfg['AMI']
    else:
        ami = prompt_image(cur_images)
    logger.debug("AMI ID: {}".format(ami))

    # prompt for key pair
    if 'KEYPAIR' in asg_cfg:
        keypair = asg_cfg['KEYPAIR']
    else:
        keypair = prompt_keypair(cur_keypairs)
    logger.debug("key pair: {}".format(keypair))

    # prompt for roles
    use_role = False
    if 'USE_ROLE' in asg_cfg:
        use_role = asg_cfg['USE_ROLE']
    else:
        use_role = prompt(get_prompt_tokens=lambda x: [(Token, "Do you want to use instance roles [y/n]: ")],
                          validator=YesNoValidator(), style=prompt_style).strip() == 'y'
    logger.debug("use_role: {} {}".format(use_role, type(use_role)))
    if use_role:
        if 'ROLE' in asg_cfg:
            role = asg_cfg['ROLE']
        else:
            role = prompt_roles(cur_roles)
        logger.debug("role: {}".format(role))

    # prompt for security groups
    if 'SECURITY_GROUPS' in asg_cfg and 'VPC' in asg_cfg:
        sgs = asg_cfg.get('SECURITY_GROUPS', [])
        vpc_id = asg_cfg.get('VPC', None)
    else:
        sgs, vpc_id = prompt_secgroup(cur_sgs)
    logger.debug("security groups: {}".format(sgs))
    logger.debug("VPC ID: {}".format(vpc_id))

    # get current AZs
    cur_azs = { i['ZoneName']: i for i in get_azs(ec2) }
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

    # check asgs that need to be configured
    instance_types = conf.get('INSTANCE_TYPES').split() if 'INSTANCE_TYPES' in conf._cfg else None
    instance_bids = conf.get('INSTANCE_BIDS').split() if 'INSTANCE_BIDS' in conf._cfg else None
    for i, queue in enumerate([i.strip() for i in conf.get('QUEUES').split()]):
        asg = "{}-{}".format(conf.get('VENUE'), queue)
        if asg in cur_asgs:
            print("ASG {} already exists. Skipping.".format(asg))
            continue

        print_component_header("Configuring autoscaling group:\n{}".format(asg))

        # get user data
        user_data = "BUNDLE_URL=s3://{}/{}-{}.tbz2".format(conf.get('CODE_BUCKET'),
                                                           queue, conf.get('VENUE'))

        # prompt instance type
        if instance_types is None:
            instance_type = prompt(get_prompt_tokens=lambda x: [(Token, "Refer to https://www.ec2instances.info/ "),
                                                                (Token, "and enter instance type to use for launch "),
                                                                (Token, "configuration: ")], style=prompt_style,
                                                                validator=Ec2InstanceTypeValidator()).strip()
        else:
            instance_type = instance_types[i]
        logger.debug("instance type: {}".format(instance_type))

        # use spot?
        market = "ondemand"
        spot_bid = None
        if instance_bids is None:
            use_spot = prompt(get_prompt_tokens=lambda x: [(Token, "Do you want to use spot instances [y/n]: ")],
                              validator=YesNoValidator(), style=prompt_style).strip() == 'y'
            if use_spot:
                market = "spot"
                spot_bid = prompt(get_prompt_tokens=lambda x: [(Token, "Enter spot price bid: ")],
                                  style=prompt_style, validator=PriceValidator()).strip()
        else:
            spot_bid = instance_bids[i]
            market = 'spot'
            if eval(spot_bid) == 0.:
                market = 'ondemand'
                spot_bid = None
        if market == 'spot':
            logger.debug("spot price bid: {}".format(spot_bid))

        # get block device mappings and remove encrypteed flag for spot to fire up
        bd_maps = cur_images[ami]['BlockDeviceMappings']
        for bd_map in bd_maps:
            if 'Ebs' in bd_map and 'Encrypted' in bd_map['Ebs']:
                del bd_map['Ebs']['Encrypted']

        # get launch config
        lc_args = {
            'ImageId': ami,
            'KeyName': keypair,
            #'IamInstanceProfile': role,
            'SecurityGroups': sgs,
            'UserData': user_data,
            'InstanceType': instance_type,
            'BlockDeviceMappings': bd_maps,
        }
        if use_role:
            lc_args['IamInstanceProfile'] = role

        if spot_bid is None:
            lc = "{}-{}-{}-launch-config".format(asg, instance_type, market)
        else:
            lc = "{}-{}-{}-{}-launch-config".format(asg, instance_type, market, spot_bid)
            lc_args['SpotPrice'] = spot_bid
        lc_args['LaunchConfigurationName'] = lc
        if lc in cur_lcs:
            print("Launch configuration {} already exists. Skipping.".format(lc))
        else:
            lc_info = create_lc(c, **lc_args)
            logger.debug("Launch configuration {}: {}".format(lc, pformat(lc_info)))
            print("Created launch configuration {}.".format(lc))

        # get autoscaling group config
        asg_args = {
            'AutoScalingGroupName': asg,
            'LaunchConfigurationName': lc,
            'MinSize': 0,
            'MaxSize': 0,
            'DefaultCooldown': 60,
            'DesiredCapacity': 0,
            'HealthCheckType': 'EC2',
            'HealthCheckGracePeriod': 300,
            'NewInstancesProtectedFromScaleIn': False,
            'AvailabilityZones': azs,
            'VPCZoneIdentifier': ",".join(subnets),
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': '{}-worker'.format(asg),
                    'PropagateAtLaunch': True,
                },
                {
                    'Key': 'Venue',
                    'Value': conf.get('VENUE'),
                    'PropagateAtLaunch': True,
                },
                {
                    'Key': 'Queue',
                    'Value': queue,
                    'PropagateAtLaunch': True,
                },
            ],
        }
        logger.debug("asg_args: {}".format(pformat(asg_args)))
        asg_info = create_asg(c, **asg_args)
        logger.debug("Autoscaling group {}: {}".format(asg, pformat(asg_info)))
        print("Created autoscaling group {}".format(asg))

        # add target tracking scaling policy
        policy_name = "{}-target-tracking".format(asg)
        metric_name = "JobsWaitingPerInstance-{}".format(asg)
        ttsp_args = {
            'AutoScalingGroupName': asg,
            'PolicyName': policy_name,
            'PolicyType': 'TargetTrackingScaling',
            'TargetTrackingConfiguration': {
                'CustomizedMetricSpecification': {
                    'MetricName': metric_name,
                    'Namespace': 'HySDS',
                    'Dimensions': [
                        {
                            'Name': 'AutoScalingGroupName',
                            'Value': asg,
                        },
                        {
                            'Name': 'Queue',
                            'Value': queue,
                        }
                    ],
                    'Statistic': 'Maximum'
                },
                'TargetValue': 1.0,
                'DisableScaleIn': True
            }, 
        }
        logger.debug("ttsp_args: {}".format(pformat(ttsp_args)))
        ttsp_info = c.put_scaling_policy(**ttsp_args)
        logger.debug("Target tracking scaling policy {}: {}".format(policy_name, pformat(ttsp_info)))
        print("Added target tracking scaling policy {} to {}".format(policy_name, asg))
