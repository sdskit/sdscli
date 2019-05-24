"""
SDS container orchestration functions.
"""
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import


from . import fabfile as fab
from sdscli.func_utils import get_module, get_func
from sdscli.prompt_utils import YesNoValidator, highlight, set_bar_desc
from sdscli.conf_utils import get_user_files_path, SettingsConf
from sdscli.log_utils import logger
from pygments.token import Token
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.shortcuts import prompt, print_tokens
from tqdm import tqdm
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


def init_mozart(conf, comp='mozart'):
    """"Initialize mozart component."""

    # progress bar
    with tqdm(total=2) as bar:

        # ensure venv
        set_bar_desc(bar, 'Ensuring HySDS venv')
        execute(fab.ensure_venv, comp, system_site_packages=False,
                install_supervisor=False, roles=[comp])
        bar.update()

        # initialize sdsadm
        set_bar_desc(bar, 'Initializing mozart')
        execute(fab.init_sdsadm, roles=[comp])
        bar.update()
        set_bar_desc(bar, 'Initialized mozart')


def init_comp(comp, conf):
    """Initialize component."""

    # if all, create progress bar
    if comp == 'all':

        # progress bar
        with tqdm(total=4) as bar:
            set_bar_desc(bar, "Initializing metrics")
            init_metrics(conf)
            bar.update()
            set_bar_desc(bar, "Initializing grq")
            init_grq(conf)
            bar.update()
            set_bar_desc(bar, "Initializing mozart")
            init_mozart(conf)
            bar.update()
            set_bar_desc(bar, "Initializing factotum")
            init_factotum(conf)
            bar.update()
            set_bar_desc(bar, "Initialized all")
            print("")
    else:
        if comp == 'metrics':
            init_metrics(conf)
        if comp == 'grq':
            init_grq(conf)
        if comp == 'mozart':
            init_mozart(conf)
        if comp == 'factotum':
            init_factotum(conf)


def init(comp, debug=False, force=False):
    """Initialize components."""

    # prompt user
    if not force:
        cont = prompt(get_prompt_tokens=lambda x: [(Token.Alert,
                                                    "Initializing component[s]: {}. Continue [y/n]: ".format(comp)), (Token, " ")],
                      validator=YesNoValidator(), style=prompt_style) == 'y'
        if not cont:
            return 0

    # get user's SDS conf settings
    conf = SettingsConf()

    logger.debug("Initializing %s" % comp)

    if debug:
        init_comp(comp, conf)
    else:
        with hide('everything'):
            init_comp(comp, conf)


def start_mozart(release, conf, comp='mozart'):
    """"Start mozart component."""

    # progress bar
    with tqdm(total=1) as bar:

        # start mozart
        set_bar_desc(bar, 'Starting mozart ({})'.format(release))
        execute(fab.start_sdsadm, release, roles=[comp])
        bar.update()
        set_bar_desc(bar, 'Started mozart ({})'.format(release))


def start_comp(comp, release, conf):
    """Start component."""

    # if all, create progress bar
    if comp == 'all':

        # progress bar
        with tqdm(total=4) as bar:
            set_bar_desc(bar, "Starting metrics")
            start_metrics(release, conf)
            bar.update()
            set_bar_desc(bar, "Starting grq")
            start_grq(release, conf)
            bar.update()
            set_bar_desc(bar, "Starting mozart")
            start_mozart(release, conf)
            bar.update()
            set_bar_desc(bar, "Starting factotum")
            start_factotum(release, conf)
            bar.update()
            set_bar_desc(bar, "Started all")
            print("")
    else:
        if comp == 'metrics':
            start_metrics(release, conf)
        if comp == 'grq':
            start_grq(release, conf)
        if comp == 'mozart':
            start_mozart(release, conf)
        if comp == 'factotum':
            start_factotum(release, conf)


def start(comp, release, debug=False, force=False):
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

    start_comp(comp, release, conf)


def stop_mozart(conf, comp='mozart'):
    """"Stop mozart component."""

    # progress bar
    with tqdm(total=1) as bar:

        # stop mozart
        set_bar_desc(bar, 'Stopping mozart')
        execute(fab.stop_sdsadm, roles=[comp])
        bar.update()
        set_bar_desc(bar, 'Stopped mozart')


def stop_comp(comp, conf):
    """Stop component."""

    # if all, create progress bar
    if comp == 'all':

        # progress bar
        with tqdm(total=4) as bar:
            set_bar_desc(bar, "Stopping metrics")
            stop_metrics(conf)
            bar.update()
            set_bar_desc(bar, "Stopping grq")
            stop_grq(conf)
            bar.update()
            set_bar_desc(bar, "Stopping mozart")
            stop_mozart(conf)
            bar.update()
            set_bar_desc(bar, "Stopping factotum")
            stop_factotum(conf)
            bar.update()
            set_bar_desc(bar, "Stopped all")
            print("")
    else:
        if comp == 'metrics':
            stop_metrics(conf)
        if comp == 'grq':
            stop_grq(conf)
        if comp == 'mozart':
            stop_mozart(conf)
        if comp == 'factotum':
            stop_factotum(conf)


def stop(comp, debug=False, force=False):
    """Stop components."""

    # prompt user
    if not force:
        cont = prompt(get_prompt_tokens=lambda x: [(Token.Alert,
                                                    "Stopping component[s]: {}. Continue [y/n]: ".format(comp)), (Token, " ")],
                      validator=YesNoValidator(), style=prompt_style) == 'y'
        if not cont:
            return 0

    # get user's SDS conf settings
    conf = SettingsConf()

    logger.debug("Stopping %s" % comp)

    stop_comp(comp, conf)


def logs_comp(comp, conf, follow):
    """Show logs for component."""

    execute(fab.logs_sdsadm, follow, roles=[comp])


def logs(comp, debug=False, follow=False):
    """Show logs for components."""

    # get user's SDS conf settings
    conf = SettingsConf()

    logs_comp(comp, conf, follow)
