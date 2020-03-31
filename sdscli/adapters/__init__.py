from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from sdscli.conf_utils import SettingsConf
from sdscli.log_utils import logger
from hysds_commons.elasticsearch_utils import ElasticsearchUtility


conf = SettingsConf()

_mozart_es_url = "http://{}:9200".format(conf.get('MOZART_ES_PVT_IP'))
_grq_es_url = "http://{}:9200".format(conf.get('GRQ_ES_PVT_IP'))

mozart_es = ElasticsearchUtility(_mozart_es_url, logger)
grq_es = ElasticsearchUtility(_grq_es_url, logger)
