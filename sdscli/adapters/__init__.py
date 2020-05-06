from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from sdscli.conf_utils import SettingsConf

try:
    conf = SettingsConf()
except Exception as e:
    pass
