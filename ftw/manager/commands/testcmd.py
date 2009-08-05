
import sys
from ftw.manager.commands import basecommand
from ftw.manager.commands import zopeinstance
from ftw.manager.utils import runcmd
from ftw.manager.utils import subversion as svn

class TestCommand(basecommand.BaseCommand):
    """
    Runs the tests for the current package.
    This command only works if you are in a checkout directory of
    your package and the this directory is part of a buildout.
    """

    command_name = 'test'
    command_shortcut = 't'
    description = 'Run tests for current package'

    def __call__(self):
        package_name = svn.get_package_name('.')
        sys.argv = [sys.argv[0], 'zopeinstance', 'test', '-s', package_name]
        zopeinstance.ZopeInstanceCommand(self.maincommand)()

basecommand.registerCommand(TestCommand)


