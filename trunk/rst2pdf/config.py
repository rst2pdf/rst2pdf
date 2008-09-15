# -*- coding: utf-8 -*-

# Singleton config object

import ConfigParser
import os
from simplejson import dumps, loads

cfdir=os.path.join(os.path.expanduser('~'),'.rst2pdf')
cfname=os.path.join(cfdir,'config')

def getValue(section,key,default=None):
  section=section.lower()
  key=key.lower()
  try:
    return loads(conf.get (section,key))
  except:
    return default

class ConfigError(Exception):
  def __init__(self,modulename,msg):
    self.modulename=modulename
    self.msg=msg


conf=ConfigParser.SafeConfigParser()
if not os.path.isdir(cfdir):
  os.mkdir(cfdir)

conf.read(cfname)
