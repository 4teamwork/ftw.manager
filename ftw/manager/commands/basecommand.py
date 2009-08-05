
import sys
from ftw.manager.ftwCommand import FTWCommand
from optparse import OptionParser

def registerCommand(command_cls):
    FTWCommand.registerCommand(command_cls)

class BaseCommand(object):
    """
    Long Description
    """

    command_name = None
    command_shortcut = None
    description = None
    usage = '%%prog %s [options]' % command_name

    def __init__(self, maincommand):
        self.maincommand = maincommand
        self.parser = OptionParser(version=self.maincommand.version, usage=self.usage)
        self.register_options()
        self.extend_usage()
        self.options, self.args = self.parser.parse_args(args=sys.argv[2:])

    def register_options(self):
        pass

    def extend_usage(self):
        usage = self.parser.get_usage()
        usage += self.__class__.__doc__
        self.parser.set_usage(usage)

    def __call__(self):
        raise NotImplemented

