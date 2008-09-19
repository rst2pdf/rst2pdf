# -*- coding: utf-8 -*-

import logging,sys

log = logging.getLogger('rst2pdf')
hdlr = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(levelname)s] %(filename)s L%(lineno)d %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.WARNING)
