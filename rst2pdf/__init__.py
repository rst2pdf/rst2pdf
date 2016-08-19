from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
# See LICENSE.txt for licensing terms
try:
    import pkg_resources
    try:
        version = pkg_resources.get_distribution('rst2pdf').version
    except pkg_resources.ResolutionError:
        version = None
except ImportError:
    version = None
