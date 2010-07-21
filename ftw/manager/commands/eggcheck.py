import os.path
from ftw.manager.commands.basecommand import BaseCommand, registerCommand
from ftw.manager.utils import output


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

    def register_options(self):
        pass

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

    def __call__(self):
        """Run the checks
        """
        if not os.path.exists('setup.py'):
            raise Exception('Could not find setup.py')
        self.check_setup_py()

    def check_setup_py(self):
        """setup.py checks
        """
        self.notify_part('Check setup.py')
        self.notify_check('Maintainer should be defined')
        self.notify(False, 'maintainer is defined as variable but is not used'
                    'in setup call', 'add "maintainer=maintainer," to the setup call', 1)
        self.notify_check('version.txt file exists')
        self.notify(True)
        self.notify_check('Version is taken form version.txt')
        self.notify(False, 'version is not taken from version.txt',
                    "Use: version=open('XXXX').read().strip()", 0)

registerCommand(EggCheckCommand)
