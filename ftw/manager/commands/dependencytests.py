
import os
import sys

from ftw.manager.commands import basecommand
from ftw.manager.commands import zopeinstance

class DependencyTestsCommand(basecommand.BaseCommand):
    """
    Used to run all tests of direct dependencies.
    This command requires a dependencies.txt file.
    """

    command_name = 'dependencytests'
    command_shortcut = 'dt'
    description = 'Run tests for dependencies found in dependencies.txt'
    usage = 'ftw %s' % command_name

    def __call__(self):
        if not os.path.isfile('dependencies.txt'):
            output.error('File not found: ./dependencies.txt', exit=1)
        # read dependencies
        dependencies = open('dependencies.txt').read().strip().split('\n')
        for row in dependencies:
            # remove version fix, if existing
            pkg_name = row.split('=')[0].split('>')[0].split('<')[0]
            sys.argv = [sys.argv[0], 'zopeinstance', 'test', '-s', pkg_name]
            zopeinstance.ZopeInstanceCommand(self.maincommand)()

basecommand.registerCommand(DependencyTestsCommand)

