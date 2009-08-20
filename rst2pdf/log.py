# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

import logging
import sys

logging.basicConfig(
    format='[%(levelname)s] %(filename)s:%(lineno)d %(message)s',
    level=logging.WARNING)

log = logging.getLogger('rst2pdf')
