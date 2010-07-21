from ftw.manager.commands.basecommand import BaseCommand, registerCommand
from ftw.manager.utils import output, input, scm, runcmd_with_exitcode
import distutils.core
import os.path
import sys

WIKI_PYTHON_EGGS = 'http://devwiki.4teamwork.ch/PythonEggs'


class EggCheckCommand(BaseCommand):
    """The command `eggcheck` checks if the egg has some common problems.

    Checks:
    * setup.py
    ** maintainer should be defined
    ** version should be read from version.txt, which sould exist
    ** package namespaces shouls be defined properly (they are usually
    wrong after renaming packages)
    ** various metadata stuff
    """

    command_name = 'eggcheck'
    command_shortcut = 'ec'
    description = 'Check some common problems on a egg'
    usage = 'ftw %s [OPTIONS]' % command_name

    PROBLEM_LEVELS = (
        ('ERROR', output.BOLD_ERROR),
        ('WARNING', output.BOLD_WARNING),
        ('PROBLEM', output.WARNING)
        )

    def __call__(self):
        """Run the checks
        """
        if not os.path.exists('setup.py'):
            raise Exception('Could not find setup.py')
        if scm.has_local_changes('.'):
            output.error('You have local changes, please commit them first.',
                         exit=True)
        self.check_setup_py()

    def register_options(self):
        pass

    @property
    def egginfo(self):
        """Returns a distuls setup instance
        """
        try:
            return self._egg_info
        except AttributeError:
            self._egg_info = distutils.core.run_setup('setup.py')
            return self._egg_info

    def check_setup_py(self):
        """setup.py checks
        """
        self.notify_part('Check setup.py')

        # MAINTAINER
        self.notify_check('Maintainer should be defined')
        maintainer = self.egginfo.get_maintainer()
        if maintainer and maintainer!='UNKNOWN':
            self.notify(True)
        else:
            if len(filter(lambda row:row.startswith('maintainer'),
                          open('setup.py').read().split('\n'))) > 0:
                self.notify(False, 'maintainer is defined as variable but is not used '
                            'in setup call', 'add "maintainer=maintainer," to the setup call', 1)
                if input.prompt_bool('Should I try to fix it?'):
                    rows = open('setup.py').read().split('\n')
                    file_ = open('setup.py', 'w')
                    found = False
                    for i, row in enumerate(rows):
                        file_.write(row)
                        if i != len(rows) - 1:
                            file_.write('\n')
                        if row.strip().startswith('author_email='):
                            file_.write(' ' * 6)
                            file_.write('maintainer=maintainer,')
                            file_.write('\n')
                            found = True
                    file_.close()
                    if not found:
                        output.error('Could not find keyword author_email in your setup.py, '
                                     'you have to fix it manually, sorry.', exit=1)
                    else:
                        self._validate_setup_py()
                        scm.add_and_commit_files('setup.py: register maintainer',
                                                 'setup.py')
                        print output.colorize('Fix completed successfully', output.INFO)
                    print ''
            else:
                self.notify(False, 'maintainer is not defined in the egg at all',
                            'check %s on how to define a maintainer' % WIKI_PYTHON_EGGS)

        # VERSION.TXT
        self.notify_check('version.txt file exists')
        versiontxt_path = scm.get_package_name('.').replace('.', '/') + '/version.txt'
        if os.path.exists(versiontxt_path) and os.path.isfile(versiontxt_path):
            self.notify(True)
        elif os.path.exists(versiontxt_path):
            self.notify(False, '%s exists but is not a file !?' % versiontxt_path,
                        'it should be a file containing the package version', 0)
        else:
            self.notify(False, '%s does not exist' % versiontxt_path)
            if input.prompt_bool('Should I try to fix it?'):
                version = self.egginfo.get_version()
                file_ = open(versiontxt_path, 'w')
                file_.write(version)
                file_.close()
                scm.add_and_commit_files('Added version.txt file', versiontxt_path)
                print output.colorize('Fix completed successfully', output.INFO)
                print ''

        # Version
        self.notify_check('Version is taken form version.txt')
        rows = open('setup.py').read().split('\n')
        version_rows = filter(lambda row:row.startswith('version ='), rows)
        if len(version_rows) != 1:
            self.notify(False, 'I\'m confused, it seems that you have a mess with '
                        'your versions.',
                        'check %s on how to define versions properly' % WIKI_PYTHON_EGGS)
        elif not version_rows[0].startswith('version = open('):
            self.notify(False, 'I\'m guessing that the version in your setup.py is not '
                        'taken from %s' % versiontxt_path,
                        'check %s on how to define versions properly' % WIKI_PYTHON_EGGS)
            if input.prompt_bool('Should I try to fix it?'):
                new_version_row = "version = open('%s').read().strip()" % versiontxt_path
                rows[rows.index(version_rows[0])] = new_version_row
                file_ = open('setup.py', 'w')
                file_.write('\n'.join(rows))
                file_.close()
                self._validate_setup_py()
                scm.add_and_commit_files('setup.py: using version.txt', 'setup.py')
        else:
            self.notify(True)

    def notify_part(self, part_title):
        """Print a part heading to the stdout
        """
        print ''
        output.part_title(part_title)
        print ''

    def notify_check(self, title):
        """Print check-title to the stdout
        """
        print output.colorize('CHECK:', output.BOLD_INFO), \
            output.colorize(title, output.INFO)

    def notify(self, state, problem='', solution='', problem_level=0):
        """Notify the user of a problem
        """
        if state:
            print '  OK'
        else:
            prob_type, prob_color = self.PROBLEM_LEVELS[problem_level]
            print ' ', output.colorize(prob_type, prob_color), \
                output.colorize(problem, prob_color)
            if solution:
                print '  SOLUTION:', solution
        print ''

    def _validate_setup_py(self, respond=True, respond_error=True):
        """Runs the egg_info command on the ./setup.py for checking if it still
        works.

        """
        cmd = '%s setup.py egg_info' % sys.executable
        return runcmd_with_exitcode(cmd, respond=respond,
                                    respond_error=respond_error)

registerCommand(EggCheckCommand)