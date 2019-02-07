"""
Start components for HySDS.
"""


import os
import yaml
import pwd
import hashlib
import traceback
from fabric.api import execute, hide
from tqdm import tqdm

from prompt_toolkit.shortcuts import prompt, print_tokens
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.validation import Validator, ValidationError
from pygments.token import Token

from sdscli.log_utils import logger
from sdscli.conf_utils import get_user_files_path, SettingsConf
from sdscli.os_utils import validate_dir
from sdscli.prompt_utils import YesNoValidator, set_bar_desc

from . import fabfile as fab


prompt_style = style_from_dict({
    Token.Alert: 'bg:#D8060C',
    Token.Username: '#D8060C',
    Token.Param: '#3CFF33',
})


def start_mozart(conf, comp='mozart'):
    """"Start mozart component."""

    # progress bar
    with tqdm(total=2) as bar:

        # ensure venv
        set_bar_desc(bar, 'Ensuring HySDS venv')
        execute(fab.ensure_venv, comp, roles=[comp])
        bar.update()

        # start services
        set_bar_desc(bar, 'Starting mozartd')
        execute(fab.mozartd_start, roles=[comp])
        bar.update()
        set_bar_desc(bar, 'Started mozart')


def start_metrics(conf, comp='metrics'):
    """"Start metrics component."""

    # progress bar
    with tqdm(total=2) as bar:

        # ensure venv
        set_bar_desc(bar, 'Ensuring HySDS venv')
        execute(fab.ensure_venv, comp, roles=[comp])
        bar.update()

        # start services
        set_bar_desc(bar, 'Starting metricsd')
        execute(fab.metricsd_start, roles=[comp])
        bar.update()
        set_bar_desc(bar, 'Started metrics')


def start_grq(conf, comp='grq'):
    """"Start grq component."""

    # progress bar
    with tqdm(total=2) as bar:

        # ensure venv
        set_bar_desc(bar, 'Ensuring HySDS venv')
        execute(fab.ensure_venv, 'sciflo', roles=[comp])
        bar.update()

        # start services
        set_bar_desc(bar, 'Starting grqd')
        execute(fab.grqd_start, roles=[comp])
        bar.update()
        set_bar_desc(bar, 'Started grq')


def start_factotum(conf, comp='factotum'):
    """"Start factotum component."""

    # progress bar
    with tqdm(total=2) as bar:

        # ensure venv
        set_bar_desc(bar, 'Ensuring HySDS venv')
        execute(fab.ensure_venv, 'verdi', roles=[comp])
        bar.update()

        # start services
        set_bar_desc(bar, 'Starting verdid')
        execute(fab.verdid_start, roles=[comp])
        bar.update()
        set_bar_desc(bar, 'Started factotum')


def start_comp(comp, conf):
    """Start component."""

    # if all, create progress bar
    if comp == 'all':

        # progress bar
        with tqdm(total=4) as bar:
            set_bar_desc(bar, "Starting grq")
            start_grq(conf)
            bar.update()
            set_bar_desc(bar, "Starting mozart")
            start_mozart(conf)
            bar.update()
            set_bar_desc(bar, "Starting metrics")
            start_metrics(conf)
            bar.update()
            set_bar_desc(bar, "Starting factotum")
            start_factotum(conf)
            bar.update()
            set_bar_desc(bar, "Started all")
            print("")
    else:
        if comp == 'grq':
            start_grq(conf)
        if comp == 'mozart':
            start_mozart(conf)
        if comp == 'metrics':
            start_metrics(conf)
        if comp == 'factotum':
            start_factotum(conf)


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
        start_comp(comp, conf)
    else:
        with hide('everything'):
            start_comp(comp, conf)
