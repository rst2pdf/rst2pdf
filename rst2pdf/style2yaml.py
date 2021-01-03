#!/usr/bin/env python3
# SPDX-License-Identifier: MIT

"""Convert older RSON stylesheets to YAML format

Run the script with this list of filenames to convert. It outputs to stdout, or
use the --save3 flag to have it create .yaml files
"""

import argparse
import json
import os

import yaml

from rst2pdf.dumpstyle import fixstyle
from rst2pdf.rson import loads as rloads


def main():
    # set up the command, optional --save parameter, and a list of paths
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save .yaml version of the file (rather than output to stdout)',
    )
    parser.add_argument(
        'paths',
        metavar='PATH',
        nargs='+',
        help='An RSON-formatted file to convert.',
    )
    args = parser.parse_args()

    # loop over the files
    for path in args.paths:
        # read rson from a file
        with open(path, 'rb') as fh:
            style_data = fixstyle(rloads(fh.read()))

        # output the style as json (already supported), then parse that
        json_style = json.dumps(style_data)
        reparsed_style = json.loads(json_style)

        yaml_style = yaml.dump(reparsed_style, default_flow_style=None)

        # output the yaml or save to a file
        if args.save:
            new_path = '.'.join((os.path.splitext(path)[0], 'yaml'))

            if os.path.exists(new_path):
                print("File " + new_path + " exists, cannot overwrite")
            else:
                print("Creating file " + new_path)
                with open(new_path, 'w') as file:
                    file.write(yaml_style)
        else:
            print("# " + os.path.splitext(path)[0])
            print("---")
            print(yaml_style)


if __name__ == '__main__':
    main()
