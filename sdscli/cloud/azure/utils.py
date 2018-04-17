from __future__ import absolute_import
from __future__ import print_function

import os, sys, azure.common
from azure.storage import CloudStorageAccount
from azure.storage.blob import BlockBlobService

from sdscli.log_utils import logger


def is_configured():
    """Return if Azure account is configured."""

    if config.IS_EMULATED'
        account = CloudStorageAccount(is_emulated=True)
    else:
        account = CloudStorageAccount(account_name=config.STORAGE_ACCOUNT_NAME, account_key=config.STORAGE_ACCOUNT_KEY)
        
        # Create a Block Blob Service Object
        blockblob_service = account.create_block_blob_service()

def cloud_config_check(func):
    """Wrapper function to perform cloud config check."""

    def wrapper(*args, **kwargs):
        if is_configured():
            return func(*args, **kwargs)
        else:
            logger.error("Not configured for AWS.")
            sys.exit(1)
    return wrapper


@cloud_config_check
def get_buckets(c=None, **kargs):
    """List all containers."""

    containers = blockblob_service.list_containers()
    container_list = []
    for c in containers:
        container_list.append(c.name)

    return container_list


@cloud_config_check
def get_bucket(bucket_name, c=None, **kargs):
    """Get bucket."""

    if c is None: c = boto3.resource('s3')
    return c.Bucket(bucket_name)
