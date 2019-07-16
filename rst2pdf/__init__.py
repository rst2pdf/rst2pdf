# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: MIT

try:
    import pkg_resources
    try:
        version = pkg_resources.get_distribution('rst2pdf').version
    except pkg_resources.ResolutionError:
        version = None
except ImportError:
    version = None
