# -*- coding: utf8 -*-

from ftw.manager.commands import basecommand
from ftw.manager.utils import output
from ftw.manager.utils import runcmd
from ftw.manager.utils import scm
from ftw.manager.utils import git



class SwitchCommand(basecommand.BaseCommand):
    """
    Wandelt ein lokales SVN-Repository in ein GIT-SVN-Repository um,
    oder umgekehrt.
    Es wird ein lokaler SVN-Cache unter ~/.gitsvn angelegt, welcher
    Kopien der GIT-SVN-Repositories enthält. Dies erlaubt einen schnellen
    Wechesel zwischen SVN und GIT.

    Dieser Befehl sollte im Root-Verzeichnis eines Packages ausgeführt werden.

    Pushen mit GIT-SVN:
        git svn dcommit

    Pullen mit GIT-SVN:
        git svn fetch
        git svn rebase
    """

    command_name = 'switch'
    command_shortcut = 'sw'
    description = 'Wechselt zwischen lokalem SVN- und GIT-SVN-Repository'
    usage = 'ftw %s' % command_name

    def __call__(self):
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
        svn_url = scm.get_svn_url('.')
        # check location
        if not scm.is_package_root('.'):
            output.error('Please run this command at the root of the package' +\
                         '(trunk folder, branch, tag)', exit=True)
        # check changes
        if scm.has_local_changes('.'):
            output.error('You have local changes, commit them first..', exit=True)

    def switch_to_git(self):
        output.part_title('Switching to GIT')
        url = scm.get_svn_url('.')
        runcmd('rm -rf * .*')
        git.checkout_gitsvn(url, location='..')
        git.apply_svn_ignores('.')

    def switch_to_svn(self):
        output.part_title('Switching to SVN')
        svn_url = scm.get_svn_url('.')
        runcmd('rm -rf * .*')
        runcmd('svn co %s .' % svn_url)

basecommand.registerCommand(SwitchCommand)
