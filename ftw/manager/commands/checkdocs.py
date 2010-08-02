from StringIO import StringIO
from docutils.core import publish_file
from ftw.manager.commands import basecommand
from ftw.manager.utils import output
from ftw.manager.utils import runcmd_with_exitcode
from ftw.manager.utils.memoize import memoize
import distutils.core
import os
import re
import sys


class CheckdocsCommand(basecommand.BaseCommand):
    u"""
    Checks if the description defined in setup.py is reStructured Text valid.

    This command requires docutils to be installed in the site-packes of
    your python version.

    """

    command_name = u'checkdocs'
    command_shortcut = u'cd'
    description = u'Checks if the description defined in setup.py is ' + \
        u'reStructured Text valid.'
    usage = u'ftw %s' % command_name

    def __call__(self):
        if not os.path.isfile('setup.py'):
            output.error('File not found: %s' % os.path.abspath('setup.py'),
                         exit=1)
        cmd = '%s setup.py check --restructuredtext --strict' % sys.executable
        if self.options.show:
            self.show_description()
            return
        elif self.options.browser:
            description = '\n'.join(self.get_description())
            response = open('long_description.html', 'w+')
            publish_file(writer_name='html',
                         destination=response,
                         source=StringIO(description))
            runcmd_with_exitcode('open long_description.html')
            return
        code, response, error = runcmd_with_exitcode(cmd, log=True,
                                                     respond=True,
                                                     respond_error=True)
        if code == 0:
            print '* docs okay'
        else:
            xpr = re.compile('\(line ([\d]*)\)')
            description = self.get_description()
            error = error.strip().split('\n')
            for err in error:
                print output.colorize(err, output.ERROR)
                line = xpr.search(err)
                if line:
                    line_nr = int(line.groups()[0]) - 1
                    start_line = line_nr - self.options.offrows
                    start_line = start_line > 0 and start_line or 0
                    end_line = line_nr + self.options.offrows + 1
                    end_line = end_line < len(description) and \
                        end_line or len(description)
                    line_range = range(start_line, end_line)
                    self.show_description(line_range, higlight=line_nr)
                    print ''

    @memoize
    def get_description(self):
        """ Get long description
        """
        egg = distutils.core.run_setup('setup.py')
        return egg.get_long_description().split('\n')

    def show_description(self, rows=None, higlight=None):
        description = self.get_description()
        if not rows:
            rows = range(len(description))
        for i in rows:
            p = '%i:' % (i + 1) + ' ' + description[i]
            if i == higlight:
                print output.colorize(p, output.WARNING)
            else:
                print p

    def register_options(self):
        self.parser.add_option('-s', '--show-description', dest='show',
                               action='store_true', default=False,
                               help='show long-description of setup.py ' +\
                                   '(with line numbers)')
        self.parser.add_option('-b', '--show-inbrowser', dest='browser',
                               action='store_true', default=False,
                               help='Show description converted into HTML ' +\
                                   'in your default browser')
        self.parser.add_option('-o', '--off-rows', dest='offrows',
                               action='store', type='int', default=2,
                               help='show N rows before and after a bad ' +\
                                   'row (only if not using -s)')

basecommand.registerCommand(CheckdocsCommand)
