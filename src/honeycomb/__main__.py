#!/usr/bin/env python
# * coding: utf8 *
'''
honeycomb 🐝

Usage:
    ...

Arguments:
    ...

Examples:
    ...
'''

from docopt import docopt
import sys


def main():
    args = docopt(__doc__, version='0.0.0')

    print(args)


if __name__ == '__main__':
    sys.exit(main())
