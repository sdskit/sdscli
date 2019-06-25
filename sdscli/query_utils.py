from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


from future import standard_library

standard_library.install_aliases()
import os
import sys
import json
import requests
import logging
import traceback
import backoff
from requests.packages.urllib3.exceptions import (
    InsecureRequestWarning,
    InsecurePlatformWarning,
)

from sdscli.log_utils import logger


# backoff settings
BACKOFF_MAX_VALUE = 64
BACKOFF_MAX_TRIES = 10


def build_query(ands=None, ors=None, sort_order="desc"):
    """Build ES query."""

    # build musts
    must = []
    if ands is not None:
        for k, v in ands:
            must.append({"term": {k: v}})

    # build shoulds
    should = []
    if ors is not None:
        for k, v in ors:
            should.append({"term": {k: v}})

    # build query
    query = {
        "query": {"bool": {}},
        "sort": [{"_timestamp": {"order": sort_order}}],
        "partial_fields": {"partial": {"exclude": ["city", "context"]}},
    }
    if len(must) > 0:
        query["query"]["bool"]["must"] = must
    if len(should) > 0:
        if len(must) > 0:
            must.append({"bool": {"should": should}})
        else:
            query["query"]["bool"]["should"] = should
    return query


@backoff.on_exception(
    backoff.expo, Exception, max_tries=BACKOFF_MAX_TRIES, max_value=BACKOFF_MAX_VALUE
)
def run_query(url, idx, query, doc_type=None):
    """Query ES index."""

    if doc_type is None:
        query_url = "{}/{}/_search?search_type=scan&scroll=60&size=100".format(url, idx)
    else:
        query_url = "{}/{}/{}/_search?search_type=scan&scroll=60&size=100".format(
            url, idx, doc_type
        )
    logger.info("url: {}".format(url))
    logger.info("idx: {}".format(idx))
    logger.info("doc_type: {}".format(doc_type))
    logger.info("query: {}".format(json.dumps(query, indent=2)))
    r = requests.post(query_url, data=json.dumps(query))
    r.raise_for_status()
    scan_result = r.json()
    count = scan_result["hits"]["total"]
    scroll_id = scan_result["_scroll_id"]
    hits = []
    while True:
        r = requests.post("%s/_search/scroll?scroll=60m" % url, data=scroll_id)
        res = r.json()
        scroll_id = res["_scroll_id"]
        if len(res["hits"]["hits"]) == 0:
            break
        hits.extend(res["hits"]["hits"])
    return hits


@backoff.on_exception(
    backoff.expo, Exception, max_tries=BACKOFF_MAX_TRIES, max_value=BACKOFF_MAX_VALUE
)
def query_dataset(url, idx, id, version=None, sort_order="desc"):
    """Query dataset by id and version."""

    # get index name and url
    query_url = "{}/{}/_search?search_type=scan&scroll=60&size=100".format(url, idx)
    logger.info("url: {}".format(url))
    logger.info("idx: {}".format(idx))

    # query
    query = {
        "query": {"bool": {"must": [{"term": {"_id": id}}]}},
        "sort": [{"starttime": {"order": sort_order}}],
        "partial_fields": {"partial": {"exclude": ["city", "context"]}},
    }

    # add version constraint
    if version is not None:
        query["query"]["bool"]["must"].append({"term": {"version.raw": version}})

    logger.info("query: {}".format(json.dumps(query, indent=2)))
    r = requests.post(query_url, data=json.dumps(query))
    r.raise_for_status()
    scan_result = r.json()
    count = scan_result["hits"]["total"]
    scroll_id = scan_result["_scroll_id"]
    hits = []
    while True:
        r = requests.post("%s/_search/scroll?scroll=60m" % url, data=scroll_id)
        res = r.json()
        scroll_id = res["_scroll_id"]
        if len(res["hits"]["hits"]) == 0:
            break
        hits.extend(res["hits"]["hits"])

    return hits
