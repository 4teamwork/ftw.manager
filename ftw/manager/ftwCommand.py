"""
Main ftw command
"""

import os
import sys
import traceback
import pdb
from optparse import OptionParser


class FTWCommand(object):

    version = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'version.txt')).read().strip()
    usage = 'ftw ACTION [options]'
    commands = []

    def __init__(self):
        self.debug = False
        # sort commands
        self.commands.sort(lambda a,b:cmp(a.command_name, b.command_name))
        # setup parser
        self.parser = OptionParser(version=self.version, usage=self.usage)
        self.parser.add_option('-D', dest='debug',
                               action='store_true', default=False,
                               help='Debug mode (for any command)')
        self.extend_usage()

    def __call__(self):
        if '-D' in sys.argv:
            sys.argv.remove('-D')
            self.debug = True
        try:
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
        except SystemExit:
            pass
        except KeyboardInterrupt:
            print 'Keyboard interrupt'
        except:
            if self.debug:
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                sys.stderr.write('\nStarting pdb:\n')
                pdb.post_mortem(exc_info[2])
            else:
                raise


    def extend_usage(self):
        usage = self.parser.get_usage()
        usage += '\nACTIONS::\n\n'
        namejust = max([len(cmd.command_name) for cmd in self.commands]) + 2
        for command in self.commands:
            usage += '    %s: %s%s\n' % (
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
    commands # for pyflakes
    FTWCommand()()

if __name__=='__main__':
    main()
