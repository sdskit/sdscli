from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


from future import standard_library

standard_library.install_aliases()
from sdscli.log_utils import logger


def is_configured():
    """Return if Azure account is configured."""

    return False
