from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from sdscli.adapters.hysds.fabfile import *


#####################################
# add custom fabric functions below
#####################################

def test():
    """Test fabric function."""

    run('whoami')
