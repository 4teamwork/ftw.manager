"""
Main ftw command
"""

import os
import sys
from optparse import OptionParser


class FTWCommand(object):

    version = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'version.txt')).read().strip()
    usage = '%prog ACTION [options]'
    commands = []

    def __init__(self):
        self.parser = OptionParser(version=self.version, usage=self.usage)
        self.extend_usage()

    def __call__(self):
        if len(sys.argv)==1:
            self.parser.print_help()
        elif len(sys.argv)==2 and sys.argv[1].startswith('-'):
            self.options, self.args = self.parser.parse_args()
        else:
            command_name = sys.argv[1]
            command = self.get_command(command_name)
            if command:
                command(self)()
            else:
                self.parser.print_help()

    def extend_usage(self):
        usage = self.parser.get_usage()
        usage += '\nACTIONS:\n'
        namejust = max([len(cmd.command_name) for cmd in self.commands]) + 2
        for command in self.commands:
            usage += '  %s: %s%s\n' % (
                command.command_name.ljust(namejust),
                command.description.strip(),
                command.command_shortcut and ' [%s]' % command.command_shortcut or '',
            )
        self.parser.set_usage(usage)

    def get_command(self, command_arg):
        for command in self.commands:
            if command.command_name==command_arg or command.command_shortcut==command_arg:
                return command
        return None
        

    @classmethod
    def registerCommand(cls, command_class):
        cls.commands.append(command_class)


def main():
    from ftw.manager import commands
    FTWCommand()()

if __name__=='__main__':
    main()
