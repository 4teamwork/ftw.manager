from ftw.manager.ftwCommand import FTWCommand
from ftw.manager.utils import output
from optparse import OptionParser
import sys


def registerCommand(command_cls):
    FTWCommand.registerCommand(command_cls)


class BaseCommand(object):
    """Use a long description for each command. The description will be used
    as help message.

    """

    command_name = None
    command_shortcut = None
    description = None
    usage = 'ftw %s [options]' % command_name
    use_optparse = True

    def __init__(self, maincommand):
        self.maincommand = maincommand
        self.parser = OptionParser(version=self.maincommand.version,
                                   usage=self.usage)
        self.register_options()
        self.extend_usage()
        if self.use_optparse:
            self.options, self.args = self.parser.parse_args(args=sys.argv[2:])

    def register_options(self):
        pass

    def extend_usage(self):
        usage = self.parser.get_usage()
        usage += '    Command name:     %s\n' % output.colorize(
            self.command_name,
            output.WARNING)
        if self.command_shortcut:
            usage += '    Command shortcut: %s\n' % output.colorize(
                self.command_shortcut,
                output.WARNING)
        usage += self.__class__.__doc__
        self.parser.set_usage(usage)

    def __call__(self):
        raise NotImplemented
