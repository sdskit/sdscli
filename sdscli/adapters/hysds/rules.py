"""
SDS user rules management functions.
"""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


from builtins import open
from future import standard_library
standard_library.install_aliases()
import os
import json
import yaml
import requests
import tarfile
import shutil
import traceback
from fabric.api import execute, hide

from prompt_toolkit.shortcuts import prompt, print_tokens
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.validation import Validator, ValidationError
from pygments.token import Token

from sdscli.log_utils import logger
from sdscli.conf_utils import get_user_files_path, SettingsConf
from sdscli.query_utils import run_query
from sdscli.os_utils import validate_dir, normpath


def export(args):
    """Export HySDS user rules."""

    # get user's SDS conf settings
    conf = SettingsConf()

    # query for mozart and grq rules
    mozart_es_url = "http://{}:9200".format(conf.get('MOZART_ES_PVT_IP'))
    grq_es_url = "http://{}:9200".format(conf.get('GRQ_ES_PVT_IP'))
    rules = {}
    for comp, es_url in [('mozart', mozart_es_url), ('grq', grq_es_url)]:
        hits = run_query(es_url, "user_rules", {
            "query": {
                "match_all": {}
            }
        }, doc_type=".percolator")
        if len(hits) == 0:
            logger.error("No user rules found on {}.".format(comp))
            rules[comp] = []
        else:
            rules[comp] = [i['_source'] for i in hits]
    logger.debug("rules: {}".format(json.dumps(rules, indent=2)))

    # set export directory
    outfile = normpath(args.outfile)
    export_dir = os.path.dirname(outfile)
    logger.debug("export_dir: {}".format(export_dir))

    # create export directory
    validate_dir(export_dir)

    # dump user rules JSON
    with open(outfile, 'w') as f:
        json.dump(rules, f, indent=2, sort_keys=True)


def import_rules(args):
    """Import HySDS user rules."""

    # get user's SDS conf settings
    conf = SettingsConf()

    # user rules JSON file
    rules_file = normpath(args.file)
    if not os.path.isfile(rules_file):
        logger.error(
            "HySDS user rules file {} doesn't exist.".format(rules_file))
        return 1
    logger.debug("rules_file: {}".format(rules_file))

    # read in user rules
    with open(rules_file) as f:
        rules = json.load(f)
    logger.debug("rules: {}".format(json.dumps(
        rules_file, indent=2, sort_keys=True)))

    # get ES endpoints
    mozart_es_url = "http://{}:9200".format(conf.get('MOZART_ES_PVT_IP'))
    grq_es_url = "http://{}:9200".format(conf.get('GRQ_ES_PVT_IP'))

    # index user rules in ES
    for comp, es_url in [('mozart', mozart_es_url), ('grq', grq_es_url)]:
        for rule in rules[comp]:
            r = requests.post("{}/user_rules/.percolator/".format(es_url),
                              data=json.dumps(rule))
            logger.debug(r.content)
            r.raise_for_status()
            logger.debug(r.json())
