"""
The output module contains functionality for emproving
output with colors, tables, etc.
"""

import sys

from ftw.manager import schemes

ERROR = 'error'
BOLD_ERROR = 'error_bold'
WARNING = 'warning'
BOLD_WARNING = 'warning_bold'
INFO = 'info'
BOLD_INFO = 'info_bold'

def colorize(text, color):
    return schemes.ColorScheme().colorize(text, color)


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
        char_corner = colorize('+', ERROR)
        char_vertical = colorize('|', WARNING)
        char_horicontal = colorize('-', YELLOW)
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
    print colorize('ERROR: ', BOLD_ERROR) + colorize(msg, ERROR)
    if exit:
        sys.exit(0)

def warning(msg):
    print colorize('WARNING: ', BOLD_WARNING) + colorize(msg, WARNING)

def part_title(title):
    line = colorize('===', ERROR)
    print line, colorize(title, WARNING), line

