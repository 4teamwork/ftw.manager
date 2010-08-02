from ftw.manager.commands import basecommand
from ftw.manager.commands import zopeinstance
from ftw.manager.utils import scm
import sys


class TestCommand(basecommand.BaseCommand):
    u"""
    Runs the tests for the current package.
    This command only works if you are in a checkout directory of
    your package and the this directory is part of a buildout.

    """

    command_name = u'test'
    command_shortcut = u't'
    description = u'Run tests for current package'
    usage = u'ftw %s' % command_name

    def __call__(self):
        scm.tested_for_scms(('svn', 'gitsvn'), '.')
        package_name = scm.get_package_name('.')
        sys.argv = [sys.argv[0], 'zopeinstance', 'test', '-s', package_name]
        zopeinstance.ZopeInstanceCommand(self.maincommand)()

basecommand.registerCommand(TestCommand)
