#!/usr/bin/env python3
# SPDX-License-Identifier: MIT

"""Convert older RSON stylesheets to YAML format

Run the script with the filename to convert, it outputs to stdout
"""

import argparse
import json

import yaml

from rst2pdf.dumpstyle import fixstyle
from rst2pdf.rson import loads as rloads


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'paths',
        metavar='PATH',
        nargs='+',
        help='An RSON-formatted file to convert.',
    )
    args = parser.parse_args()
    for path in args.paths:
        # read rson from a file
        with open(path, 'rb') as fh:
            style_data = fixstyle(rloads(fh.read()))

        # output the style as json, then parse that
        json_style = json.dumps(style_data)
        reparsed_style = json.loads(json_style)

        yaml_style = yaml.dump(reparsed_style, default_flow_style=None)
        print(yaml_style)


if __name__ == '__main__':
    main()
