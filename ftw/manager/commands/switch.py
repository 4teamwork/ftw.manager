from ftw.manager.commands import basecommand
from ftw.manager.utils import git
from ftw.manager.utils import output
from ftw.manager.utils import runcmd
from ftw.manager.utils import scm
import os.path
import sys


class SwitchCommand(basecommand.BaseCommand):
    u"""
    Converts the local svn checkout into a git-svn checkout and vice versa.
    The git-svn repository is initally heavy to clone, thats why it is cached
    in `~/.gitsvn` after the first clone.

    """

    command_name = u'switch'
    command_shortcut = u'sw'
    description = u'Switch between SVN and GIT-SVN'
    usage = u'ftw %s' % command_name

    def __call__(self):
        scm.tested_for_scms(('svn', 'gitsvn'), '.')
        self.check_conditions()
        if scm.is_subversion('.'):
            self.switch_to_git()
        elif scm.is_git('.'):
            self.switch_to_svn()
        else:
            raise 'neither git nor svn !?'

    def check_conditions(self):
        output.part_title('Checking conditions')
        # check repo
        if not scm.is_scm('.'):
            output.error('Not in a local repository', exit=True)
        # check location
        if not scm.is_package_root('.'):
            output.error('Please run this command at the root of the package'
                         '(trunk folder, branch, tag)', exit=True)
        # check changes
        if scm.has_local_changes('.'):
            output.error('You have local changes, commit them first..',
                         exit=True)

    def switch_to_git(self):
        output.part_title('Switching to GIT')
        url = scm.get_svn_url('.')
        runcmd('rm -rf * .*')
        git.checkout_gitsvn(url, location='..')
        git.apply_svn_ignores('.')
        self.create_egg_info()

    def switch_to_svn(self):
        output.part_title('Switching to SVN')
        svn_url = scm.get_svn_url('.')
        runcmd('rm -rf * .*')
        runcmd('svn co %s .' % svn_url)
        self.create_egg_info()

    def create_egg_info(self):
        if os.path.exists('setup.py'):
            output.part_title('Creating egg-infos')
            runcmd('%s setup.py egg_info' % sys.executable)

basecommand.registerCommand(SwitchCommand)
