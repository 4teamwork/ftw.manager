
import os
import sys
from ftw.manager.commands import basecommand
from ftw.manager.utils import runcmd
from ftw.manager.utils import output

class CheckdocsCommand(basecommand.BaseCommand):
    """
    Checks if the description defined in setup.py is reStructured Text valid.
    """

    command_name = 'checkdocs'
    description = 'Checks if the description defined in setup.py is reStructured Text valid.'
    usage = 'ftw %s' % command_name

    def __call__(self):
        if not os.path.isfile('setup.py'):
            output.error('File not found: %s' % os.path.abspath('setup.py'),
                         exit=1)
        cmd = '%s setup.py check --restructuredtext --strict' % sys.executable
        runcmd(cmd, log=True)
basecommand.registerCommand(CheckdocsCommand)

            
