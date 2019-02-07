"""
Configuration for SDSKit cluster.
"""


import os
import yaml
import traceback

from sdscli.log_utils import logger
from sdscli.conf_utils import SettingsConf


def configure():
    """Configure SDS config file for SDSKit."""

    logger.debug("Got here for SDSKit")
    conf = SettingsConf()
    logger.debug(conf)
