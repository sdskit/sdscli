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
import asciiplotlib as apl
from fabric.api import execute, hide
import traceback
import pkgutil
import json
import os
from xmlrpc.client import ServerProxy
import ssl
import netrc
import requests
import redis
import elasticsearch
from future import standard_library

standard_library.install_aliases()


prompt_style = style_from_dict(
    {Token.Alert: "bg:#D8060C", Token.Username: "#D8060C", Token.Param: "#3CFF33"}
)


def init_mozart(conf, comp="mozart"):
    """"Initialize mozart component."""

    # progress bar
    with tqdm(total=8) as bar:

        # ensure venv
        set_bar_desc(bar, "Ensuring HySDS venv")
        execute(
            fab.ensure_venv,
            comp,
            system_site_packages=False,
            install_supervisor=False,
            roles=[comp],
        )
        bar.update()

        # initialize sdsadm
        set_bar_desc(bar, "Initializing mozart")
        execute(fab.init_sdsadm, roles=[comp])
        bar.update()
        set_bar_desc(bar, "Initialized mozart")

        # configure for cluster
        set_bar_desc(bar, "Configuring mozart")
        execute(
            fab.conf_sdsadm,
            "celeryconfig.py",
            "~/mozart/etc/celeryconfig.py",
            roles=[comp],
        )
        bar.update()
        execute(
            fab.conf_sdsadm,
            "datasets.json",
            "~/mozart/etc/datasets.json",
            True,
            roles=[comp],
        )
        bar.update()
        execute(
            fab.conf_sdsadm,
            "inet_http_server.conf",
            "~/mozart/etc/conf.d/inet_http_server.conf",
            True,
            roles=[comp],
        )
        bar.update()
        execute(
            fab.conf_sdsadm, "settings.cfg", "~/mozart/etc/settings.cfg", roles=[comp]
        )
        bar.update()
        execute(fab.conf_sdsadm, "netrc", ".netrc", roles=[comp])
        execute(fab.chmod, 600, ".netrc", roles=[comp])
        bar.update()
        execute(fab.send_awscreds, roles=[comp])
        bar.update()
        set_bar_desc(bar, "Configured mozart")


def init_grq(conf, comp="grq"):
    """"Initialize grq component."""

    # progress bar
    with tqdm(total=8) as bar:

        # ensure venv
        set_bar_desc(bar, "Ensuring HySDS venv")
        execute(
            fab.ensure_venv,
            "sciflo",
            system_site_packages=False,
            install_supervisor=False,
            roles=[comp],
        )
        bar.update()

        # rsync sdsadm
        set_bar_desc(bar, "Syncing sdsadm")
        execute(fab.rm_rf, "~/sciflo/ops/sdsadm", roles=[comp])
        execute(fab.rsync_sdsadm, roles=[comp])
        bar.update()

        # initialize sdsadm
        set_bar_desc(bar, "Initializing grq")
        execute(fab.init_sdsadm, roles=[comp])
        bar.update()
        set_bar_desc(bar, "Initialized grq")

        # configure for cluster
        set_bar_desc(bar, "Configuring grq")
        execute(
            fab.conf_sdsadm,
            "celeryconfig.py",
            "~/sciflo/etc/celeryconfig.py",
            roles=[comp],
        )
        bar.update()
        execute(
            fab.conf_sdsadm,
            "datasets.json",
            "~/sciflo/etc/datasets.json",
            True,
            roles=[comp],
        )
        bar.update()
        execute(
            fab.conf_sdsadm,
            "inet_http_server.conf",
            "~/sciflo/etc/conf.d/inet_http_server.conf",
            True,
            roles=[comp],
        )
        bar.update()
        execute(
            fab.conf_sdsadm,
            "tosca_settings.cfg",
            "~/sciflo/etc/tosca_settings.cfg",
            roles=[comp],
        )
        bar.update()
        execute(
            fab.conf_sdsadm,
            "pele_settings.cfg",
            "~/sciflo/etc/pele_settings.cfg",
            roles=[comp],
        )
        bar.update()
        netrc = os.path.join(get_user_files_path(), "netrc")
        if os.path.exists(netrc):
            set_bar_desc(bar, "Configuring netrc")
            execute(fab.send_template, "netrc", ".netrc", roles=[comp])
            execute(fab.chmod, 600, ".netrc", roles=[comp])
        execute(fab.send_awscreds, roles=[comp])
        bar.update()
        set_bar_desc(bar, "Configured grq")


def init_metrics(conf, comp="metrics"):
    """"Initialize metrics component."""

    # progress bar
    with tqdm(total=7) as bar:

        # ensure venv
        set_bar_desc(bar, "Ensuring HySDS venv")
        execute(
            fab.ensure_venv,
            comp,
            system_site_packages=False,
            install_supervisor=False,
            roles=[comp],
        )
        bar.update()

        # rsync sdsadm
        set_bar_desc(bar, "Syncing sdsadm")
        execute(fab.rm_rf, "~/{}/ops/sdsadm".format(comp), roles=[comp])
        execute(fab.rsync_sdsadm, roles=[comp])
        bar.update()

        # initialize sdsadm
        set_bar_desc(bar, "Initializing metrics")
        execute(fab.init_sdsadm, roles=[comp])
        bar.update()
        set_bar_desc(bar, "Initialized metrics")

        # configure for cluster
        set_bar_desc(bar, "Configuring metrics")
        execute(
            fab.conf_sdsadm,
            "celeryconfig.py",
            "~/metrics/etc/celeryconfig.py",
            roles=[comp],
        )
        bar.update()
        execute(
            fab.conf_sdsadm,
            "datasets.json",
            "~/metrics/etc/datasets.json",
            True,
            roles=[comp],
        )
        bar.update()
        execute(
            fab.conf_sdsadm,
            "inet_http_server.conf",
            "~/metrics/etc/conf.d/inet_http_server.conf",
            True,
            roles=[comp],
        )
        bar.update()
        netrc = os.path.join(get_user_files_path(), "netrc")
        if os.path.exists(netrc):
            set_bar_desc(bar, "Configuring netrc")
            execute(fab.send_template, "netrc", ".netrc", roles=[comp])
            execute(fab.chmod, 600, ".netrc", roles=[comp])
        execute(fab.send_awscreds, roles=[comp])
        bar.update()
        set_bar_desc(bar, "Configured metrics")


def init_factotum(conf, comp="factotum"):
    """"Initialize factotum component."""

    # progress bar
    with tqdm(total=7) as bar:

        # ensure venv
        set_bar_desc(bar, "Ensuring HySDS venv")
        execute(
            fab.ensure_venv,
            "verdi",
            system_site_packages=False,
            install_supervisor=False,
            roles=[comp],
        )
        bar.update()

        # rsync sdsadm
        set_bar_desc(bar, "Syncing sdsadm")
        execute(fab.rm_rf, "~/verdi/ops/sdsadm", roles=[comp])
        execute(fab.rsync_sdsadm, roles=[comp])
        bar.update()

        # initialize sdsadm
        set_bar_desc(bar, "Initializing factotum")
        execute(fab.init_sdsadm, roles=[comp])
        bar.update()
        set_bar_desc(bar, "Initialized factotum")

        # configure for cluster
        set_bar_desc(bar, "Configuring factotum")
        execute(
            fab.conf_sdsadm,
            "celeryconfig.py",
            "~/verdi/etc/celeryconfig.py",
            roles=[comp],
        )
        bar.update()
        execute(
            fab.conf_sdsadm,
            "datasets.json",
            "~/verdi/etc/datasets.json",
            True,
            roles=[comp],
        )
        bar.update()
        execute(
            fab.conf_sdsadm,
            "inet_http_server.conf",
            "~/verdi/etc/conf.d/inet_http_server.conf",
            True,
            roles=[comp],
        )
        bar.update()
        netrc = os.path.join(get_user_files_path(), "netrc")
        if os.path.exists(netrc):
            set_bar_desc(bar, "Configuring netrc")
            execute(fab.send_template, "netrc", ".netrc", roles=[comp])
            execute(fab.chmod, 600, ".netrc", roles=[comp])
        execute(fab.send_awscreds, roles=[comp])
        bar.update()
        set_bar_desc(bar, "Configured factotum")


def init_ci(conf, comp="ci"):
    """"Initialize ci component."""

    # progress bar
    with tqdm(total=7) as bar:

        # ensure venv
        set_bar_desc(bar, "Ensuring HySDS venv")
        execute(
            fab.ensure_venv,
            "verdi",
            system_site_packages=False,
            install_supervisor=False,
            roles=[comp],
        )
        bar.update()

        # rsync sdsadm
        set_bar_desc(bar, "Syncing sdsadm")
        execute(fab.rm_rf, "~/verdi/ops/sdsadm", roles=[comp])
        execute(fab.rsync_sdsadm, roles=[comp])
        bar.update()

        # initialize sdsadm
        set_bar_desc(bar, "Initializing ci")
        execute(fab.init_sdsadm, roles=[comp])
        bar.update()
        set_bar_desc(bar, "Initialized ci")

        # configure for cluster
        set_bar_desc(bar, "Configuring ci")
        execute(
            fab.conf_sdsadm,
            "celeryconfig.py",
            "~/verdi/etc/celeryconfig.py",
            roles=[comp],
        )
        bar.update()
        execute(
            fab.conf_sdsadm,
            "datasets.json",
            "~/verdi/etc/datasets.json",
            True,
            roles=[comp],
        )
        bar.update()
        execute(
            fab.conf_sdsadm,
            "inet_http_server.conf",
            "~/verdi/etc/conf.d/inet_http_server.conf",
            True,
            roles=[comp],
        )
        bar.update()
        netrc = os.path.join(get_user_files_path(), "netrc")
        if os.path.exists(netrc):
            set_bar_desc(bar, "Configuring netrc")
            execute(fab.send_template, "netrc", ".netrc", roles=[comp])
            execute(fab.chmod, 600, ".netrc", roles=[comp])
        execute(fab.send_awscreds, roles=[comp])
        bar.update()
        set_bar_desc(bar, "Configured ci")


def init_comp(comp, conf):
    """Initialize component."""

    if comp == "all":
        comps = ["metrics", "grq", "mozart", "factotum", "ci"]
    elif comp == "core":
        comps = ["metrics", "grq", "mozart", "factotum"]
    else:
        comps = [comp]

    with tqdm(total=len(comps)) as bar:
        for c in comps:
            set_bar_desc(bar, "Initializing {}".format(c))
            globals()["init_{}".format(c)](conf)
            bar.update()
            set_bar_desc(bar, "Initialized {}".format(c))
        set_bar_desc(bar, "Initialized {}".format(comp))
        print("")


def init(comp, debug=False, force=False):
    """Initialize components."""

    # prompt user
    if not force:
        cont = (
            prompt(
                get_prompt_tokens=lambda x: [
                    (
                        Token.Alert,
                        "Initializing component[s]: {}. Continue [y/n]: ".format(comp),
                    ),
                    (Token, " "),
                ],
                validator=YesNoValidator(),
                style=prompt_style,
            )
            == "y"
        )
        if not cont:
            return 0

    # get user's SDS conf settings
    conf = SettingsConf()

    logger.debug("Initializing %s" % comp)

    if debug:
        init_comp(comp, conf)
    else:
        with hide("everything"):
            init_comp(comp, conf)


def start_comp(comp, release, conf):
    """Start component."""

    if comp == "all":
        comps = ["metrics", "grq", "mozart", "factotum", "ci"]
    elif comp == "core":
        comps = ["metrics", "grq", "mozart", "factotum"]
    else:
        comps = [comp]
    with tqdm(total=len(comps)) as bar:
        for c in comps:
            set_bar_desc(bar, "Starting {} ({})".format(c, release))
            execute(fab.start_sdsadm, release, roles=[c])
            bar.update()
            set_bar_desc(bar, "Started {} ({})".format(c, release))
        set_bar_desc(bar, "Started all")
        print("")


def start(comp, release, debug=False, force=False):
    """Start components."""

    # prompt user
    if not force:
        cont = (
            prompt(
                get_prompt_tokens=lambda x: [
                    (
                        Token.Alert,
                        "Starting component[s]: {}. Continue [y/n]: ".format(comp),
                    ),
                    (Token, " "),
                ],
                validator=YesNoValidator(),
                style=prompt_style,
            )
            == "y"
        )
        if not cont:
            return 0

    # get user's SDS conf settings
    conf = SettingsConf()

    logger.debug("Starting %s" % comp)

    start_comp(comp, release, conf)


def stop_comp(comp, conf):
    """Stop component."""

    if comp == "all":
        comps = ["metrics", "grq", "mozart", "factotum", "ci"]
    elif comp == "core":
        comps = ["metrics", "grq", "mozart", "factotum"]
    else:
        comps = [comp]
    with tqdm(total=len(comps)) as bar:
        for c in comps:
            set_bar_desc(bar, "Stopping {}".format(c))
            execute(fab.stop_sdsadm, roles=[c])
            bar.update()
            set_bar_desc(bar, "Stopped {}".format(c))
        set_bar_desc(bar, "Stopped all")
        print("")


def stop(comp, debug=False, force=False):
    """Stop components."""

    # prompt user
    if not force:
        cont = (
            prompt(
                get_prompt_tokens=lambda x: [
                    (
                        Token.Alert,
                        "Stopping component[s]: {}. Continue [y/n]: ".format(comp),
                    ),
                    (Token, " "),
                ],
                validator=YesNoValidator(),
                style=prompt_style,
            )
            == "y"
        )
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

    if comp == "all":
        comps = ["metrics", "grq", "mozart", "factotum", "ci"]
    elif comp == "core":
        comps = ["metrics", "grq", "mozart", "factotum"]
    else:
        comps = [comp]
    for c in comps:
        execute(fab.ps_sdsadm, roles=[c])


def ps(comp, debug=False):
    """List containers for components."""

    # get user's SDS conf settings
    conf = SettingsConf()

    ps_comp(comp, conf)


def run_comp(comp, cmd, conf):
    """Run command in component."""

    execute(fab.run_sdsadm, cmd, roles=[comp])


def run(comp, cmd):
    """Run command in components."""

    # get user's SDS conf settings
    conf = SettingsConf()

    run_comp(comp, cmd, conf)


def rabbitmq_healthy(ip, u, p):
    """Return True if RabbitMQ is healthy. False otherwise."""

    url = "http://{}:{}@{}:15672/api/healthchecks/node".format(u, p, ip)
    try:
        r = requests.get(url)
        r.raise_for_status()
        info = r.json()
        logger.debug(json.dumps(info))
        if info["status"] == "ok":
            return True
        elif info["status"] == "failed":
            logger.debug("reason: {}".format(info["reason"]))
            return False
        else:
            logger.debug("Unknown status: {}".format(info["status"]))
            return False
    except Exception as e:
        logger.debug("Error: {}".format(e))
        return False


def es_healthy(ip):
    """Return True if Elasticsearch is healthy. False otherwise."""

    try:
        es = elasticsearch.Elasticsearch([ip], verify_certs=False)
        es.ping()
        return True
    except Exception as e:
        logger.debug("Error: {}".format(e))
        return False


def redis_healthy(ip, password=None):
    """Return True if Redis is healthy. False otherwise."""

    try:
        r = redis.StrictRedis(ip, password=password)
        r.ping()
        return True
    except Exception as e:
        logger.debug("Error: {}".format(e))
        return False


def status_comp(comp, conf):
    """List containers for component."""

    if comp == "all":
        comps = ["metrics", "grq", "mozart", "factotum", "ci"]
    elif comp == "core":
        comps = ["metrics", "grq", "mozart", "factotum"]
    else:
        comps = [comp]
    for c in comps:
        nc = netrc.netrc().hosts
        comp_ip = conf.get("{}_PVT_IP".format(c.upper()))

        # third-party software status
        tps_health = [["component", "service", "healthy"]]
        if c == "mozart":
            # rabbitmq
            if "mozart-rabbitmq" in nc:
                rabbit_u, rabbit_a, rabbit_p = nc["mozart-rabbitmq"]
            else:
                rabbit_u, rabbit_a, rabbit_p = nc[comp_ip]
            tps_health.append(
                [c, "rabbitmq", rabbitmq_healthy(comp_ip, rabbit_u, rabbit_p)]
            )

        if c in ("mozart", "grq", "metrics"):
            # elasticsearch
            tps_health.append([c, "elasticsearch", es_healthy(comp_ip)])

        if c in ("mozart", "grq", "metrics"):
            # redis
            if "{}-redis".format(c) in nc:
                redis_u, redis_a, redis_p = nc["{}-redis".format(c)]
            else:
                redis_p = None
            tps_health.append([c, "redis", redis_healthy(comp_ip, redis_p)])

        if len(tps_health) > 1:
            fig = apl.figure()
            fig.table(tps_health)
            fig.show()

        # supervisor processes
        if comp_ip in nc:
            u, a, p = nc[comp_ip]
            server_url = "https://{}:{}@{}/supervisor/RPC2".format(u, p, comp_ip)
        else:
            server_url = "https://{}/supervisor/RPC2".format(comp_ip)
        server = ServerProxy(server_url, context=ssl._create_unverified_context())
        state = server.supervisor.getState()
        logger.debug("{} state: {}".format(c, json.dumps(state, indent=2)))
        info = server.supervisor.getAllProcessInfo()
        logger.debug("{} info: {}".format(c, json.dumps(info, indent=2)))
        status_table = [["component", "group", "name", "statename", "description"]]
        for i in info:
            status_table.append(
                [c, i["group"], i["name"], i["statename"], i["description"]]
            )
        fig = apl.figure()
        fig.table(status_table)
        fig.show()


def status(comp, debug=False):
    """List containers for components."""

    # get user's SDS conf settings
    conf = SettingsConf()

    status_comp(comp, conf)
