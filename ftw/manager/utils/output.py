"""
The output module contains functionality for emproving
output with colors, tables, etc.
"""

import sys

RED             = '\033[0;31m%s\033[00m'
GREEN           = '\033[0;32m%s\033[00m'
YELLOW          = '\033[0;33m%s\033[00m'
RED_BOLD        = '\033[1;31m%s\033[00m'
GREEN_BOLD      = '\033[1;32m%s\033[00m'
YELLOW_BOLD     = '\033[1;33m%s\033[00m'

class ColorString(str):

    def __new__(cls, value, color):
        self = str.__new__(cls, color % value)
        self.value = value
        self.color = color
        return self

    def __len__(self):
        return len(self.value)

    def ljust(self, width):
        s = str(self)
        if width - len(self) > 0:
            s += ' ' * (width - len(self))
        return s

class ASCIITable(object):

    def __init__(self, *titles):
        self.titles = titles
        self.rows = []

    def push(self, row):
        self.rows.append(row)

    def __call__(self):
        widths = []
        for row in [self.titles] + self.rows:
            for col, val in enumerate(row):
                if len(widths) <= col:
                    widths.append(0)
                if len(val) + 2 > widths[col]:
                    widths[col] = len(val) + 2
        char_corner = ColorString('+', RED)
        char_vertical = ColorString('|', YELLOW)
        char_horicontal = ColorString('-', YELLOW)
        def hline(sep=char_horicontal):
            chrs = [char_corner]
            for w in widths:
                chrs.append(w*sep)
                chrs.append(char_corner)
            return ''.join(chrs)
        def formatrow(row):
            chrs = [char_vertical]
            for col, val in enumerate(row):
                newval = ' ' + val.ljust(widths[col] - 1)
                chrs.append(newval)
                chrs.append(char_vertical)
            return ''.join(chrs)
        print hline()
        print formatrow(self.titles)
        print hline()
        for row in self.rows:
            print formatrow(row)
        print hline()


def error(msg, exit=False):
    print ColorString('ERROR: ', RED_BOLD) + ColorString(msg, RED)
    if exit:
        sys.exit(0)
