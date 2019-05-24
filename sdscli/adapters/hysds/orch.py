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


def init_grq(conf, comp='grq'):
    """"Initialize grq component."""

    # progress bar
    with tqdm(total=3) as bar:

        # ensure venv
        set_bar_desc(bar, 'Ensuring HySDS venv')
        execute(fab.ensure_venv, 'sciflo', system_site_packages=False,
                install_supervisor=False, roles=[comp])
        bar.update()

        # rsync sdsadm
        set_bar_desc(bar, 'Syncing sdsadm')
        execute(fab.rm_rf, '~/sciflo/ops/sdsadm', roles=[comp])
        execute(fab.rsync_sdsadm, roles=[comp])
        bar.update()

        # initialize sdsadm
        set_bar_desc(bar, 'Initializing grq')
        execute(fab.init_sdsadm, roles=[comp])
        bar.update()
        set_bar_desc(bar, 'Initialized grq')


def init_metrics(conf, comp='metrics'):
    """"Initialize metrics component."""

    # progress bar
    with tqdm(total=3) as bar:

        # ensure venv
        set_bar_desc(bar, 'Ensuring HySDS venv')
        execute(fab.ensure_venv, comp, system_site_packages=False,
                install_supervisor=False, roles=[comp])
        bar.update()

        # rsync sdsadm
        set_bar_desc(bar, 'Syncing sdsadm')
        execute(fab.rm_rf, '~/{}/ops/sdsadm'.format(comp), roles=[comp])
        execute(fab.rsync_sdsadm, roles=[comp])
        bar.update()

        # initialize sdsadm
        set_bar_desc(bar, 'Initializing metrics')
        execute(fab.init_sdsadm, roles=[comp])
        bar.update()
        set_bar_desc(bar, 'Initialized metrics')


def init_factotum(conf, comp='factotum'):
    """"Initialize factotum component."""

    # progress bar
    with tqdm(total=3) as bar:

        # ensure venv
        set_bar_desc(bar, 'Ensuring HySDS venv')
        execute(fab.ensure_venv, 'verdi', system_site_packages=False,
                install_supervisor=False, roles=[comp])
        bar.update()

        # rsync sdsadm
        set_bar_desc(bar, 'Syncing sdsadm')
        execute(fab.rm_rf, '~/verdi/ops/sdsadm', roles=[comp])
        execute(fab.rsync_sdsadm, roles=[comp])
        bar.update()

        # initialize sdsadm
        set_bar_desc(bar, 'Initializing factotum')
        execute(fab.init_sdsadm, roles=[comp])
        bar.update()
        set_bar_desc(bar, 'Initialized factotum')


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


def start_comp(comp, release, conf):
    """Start component."""

    comps = ['metrics', 'grq', 'mozart', 'factotum'] if comp == 'all' else [comp]
    with tqdm(total=len(comps)) as bar:
        for c in comps:
            set_bar_desc(bar, 'Starting {} ({})'.format(c, release))
            execute(fab.start_sdsadm, release, roles=[c])
            bar.update()
            set_bar_desc(bar, 'Started {} ({})'.format(c, release))
        set_bar_desc(bar, "Started all")
        print("")


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


def stop_comp(comp, conf):
    """Stop component."""

    comps = ['metrics', 'grq', 'mozart', 'factotum'] if comp == 'all' else [comp]
    with tqdm(total=len(comps)) as bar:
        for c in comps:
            set_bar_desc(bar, 'Stopping {}'.format(c))
            execute(fab.stop_sdsadm, roles=[c])
            bar.update()
            set_bar_desc(bar, 'Stopped {}'.format(c))
        set_bar_desc(bar, "Stopped all")
        print("")


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


def ps_comp(comp, conf):
    """List containers for component."""

    comps = ['metrics', 'grq', 'mozart', 'factotum'] if comp == 'all' else [comp]
    for c in comps:
        execute(fab.ps_sdsadm, roles=[c])


def ps(comp, debug=False):
    """List containers for components."""

    # get user's SDS conf settings
    conf = SettingsConf()

    ps_comp(comp, conf)
