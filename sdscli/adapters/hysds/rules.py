"""SDS user rules management functions."""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import open
from future import standard_library
standard_library.install_aliases()

import os
import json

from sdscli.log_utils import logger
from sdscli.os_utils import validate_dir, normpath
from hysds.es_util import get_mozart_es

USER_RULES_MOZART = 'user_rules-mozart'
USER_RULES_GRQ = 'user_rules-grq'

mozart_es = get_mozart_es()


def export(args):
    """Export HySDS user rules."""
    rules = {}

    mozart_rules = mozart_es.query(index=USER_RULES_MOZART)
    rules['mozart'] = [rule['_source'] for rule in mozart_rules]
    logger.debug('%d mozart user rules found' % len(mozart_rules))

    grq_rules = mozart_es.query(index=USER_RULES_MOZART)
    rules['grq'] = [rule['_source'] for rule in grq_rules]
    logger.debug('%d grq user rules found' % len(grq_rules))

    logger.debug("rules: {}".format(json.dumps(rules, indent=2)))

    outfile = normpath(args.outfile)  # set export directory
    export_dir = os.path.dirname(outfile)
    logger.debug("export_dir: {}".format(export_dir))

    validate_dir(export_dir)  # create export directory

    with open(outfile, 'w') as f:
        json.dump(rules, f, indent=2, sort_keys=True)  # dump user rules JSON


def import_rules(args):
    """
    Import HySDS user rules.
    rules json structure: {
        "mozart": [...],
        "grq": [...],
    }
    """

    rules_file = normpath(args.file)  # user rules JSON file
    logger.debug("rules_file: {}".format(rules_file))

    if not os.path.isfile(rules_file):
        logger.error("HySDS user rules file {} doesn't exist.".format(rules_file))
        return 1

    with open(rules_file) as f:
        user_rules = json.load(f)  # read in user rules
    logger.debug("rules: {}".format(json.dumps(rules_file, indent=2, sort_keys=True)))

    for rule in user_rules['mozart']:
        result = mozart_es.index_document(index=USER_RULES_MOZART, body=rule)  # indexing mozart rules
        logger.debug(result)

    for rule in user_rules['grq']:
        result = mozart_es.index_document(index=USER_RULES_GRQ, body=rule)  # indexing GRQ rules
        logger.debug(result)
