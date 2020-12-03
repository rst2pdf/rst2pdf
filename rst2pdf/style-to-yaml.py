#!/usr/bin/env python
'''
    Convert older RSON stylesheets to YAML format

    Run the script with the filename to convert, it outputs to stdout
'''

import sys
import json
import yaml
from rst2pdf.dumpstyle import fixstyle

from rson import loads as rloads

if __name__ == '__main__':
    fname = sys.argv[1]
    # read rson from a file
    sstr = open(fname, 'rb').read()
    style_data = fixstyle(rloads(sstr))
    # output the style as json, then parse that
    json_style = json.dumps(style_data)
    reparsed_style = json.loads(json_style)

    yaml_style = yaml.dump(reparsed_style)
    print(yaml_style)
