from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


from future import standard_library
standard_library.install_aliases()
import os
import sys
import importlib
import json
import yaml
import traceback
import argparse
import logging
from importlib import import_module

from sdscli.log_utils import logger


def get_module(mod_name):
    """Import module and return."""

    try:
        return import_module(mod_name)
    except ImportError:
        logger.error('Failed to import module "%s".' % mod_name)
        raise


def get_func(mod_name, func_name):
    """Import function and return."""

    mod = get_module(mod_name)
    logger.debug("mod: %s" % mod)
    try:
        return getattr(mod, func_name)
    except AttributeError:
        logger.error('Failed to get function "%s" from module "%s".' %
                     (func_name, mod_name))
        raise
