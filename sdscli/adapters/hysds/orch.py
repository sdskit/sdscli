"""
SDS container orchestration functions.
"""
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import


from sdscli.func_utils import get_module, get_func
from sdscli.prompt_utils import YesNoValidator, highlight
from sdscli.conf_utils import get_user_files_path, SettingsConf
from sdscli.log_utils import logger
from pygments.token import Token
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.shortcuts import prompt, print_tokens
from fabric.api import execute, hide
import traceback
import pkgutil
import json
import os
from future import standard_library
standard_library.install_aliases()


prompt_style = style_from_dict({
    Token.Alert: 'bg:#D8060C',
    Token.Username: '#D8060C',
    Token.Param: '#3CFF33',
})


def start(comp, debug=False, force=False):
    """Start components."""

    # prompt user
    if not force:
        cont = prompt(get_prompt_tokens=lambda x: [(Token.Alert,
                                                    "Starting component[s]: {}. Continue [y/n]: ".format(comp)), (Token, " ")],
                      validator=YesNoValidator(), style=prompt_style) == 'y'
        if not cont:
            return 0

    # get user's SDS conf settings
    conf = SettingsConf()

    logger.debug("Starting %s" % comp)

    if debug:
        #start_comp(comp, conf)
        logger.debug("got here: {}".format(comp))
    else:
        with hide('everything'):
            #start_comp(comp, conf)
            logger.debug("got there: {}".format(comp))
