
import os
from ftw.manager.commands import basecommand
from ftw.manager.utils import runcmd
from ftw.manager.utils import output
from ftw.manager.utils import input
from ftw.manager.utils import scm
from ftw.manager.utils import git
from ftw.manager.utils import subversion as svn

class CheckoutCommand(basecommand.BaseCommand):
    """
    Checks out a package with git-svn

    package_name : Name of the package you want to checkout
    """

    command_name = 'checkout'
    command_shortcut = 'co'
    description = 'Checks out a package with git-svn'
    usage = '%%prog %s package_name' % command_name

    def __call__(self):
        if len(self.args)==0:
            output.error('package_name is required', exit=1)
        package_name = self.args[0]
        git.setup_gitsvn_cache()
        # already checked out once?
        cache_path = os.path.join(git.get_gitsvn_cache_path(), package_name)
        if not os.path.isdir(cache_path):
            svn_url = self.get_svn_url(package_name)
            git.checkout_gitsvn(svn_url)
        else:
            # cache_path existing ; just update and clone
            runcmd('cd %s; git reset --hard' % cache_path)
            runcmd('cd %s; git svn fetch' % cache_path)
            runcmd('cd %s; git svn rebase' % cache_path)
            runcmd('cp -r %s .' % cache_path)
            runcmd('cd %s ; git checkout %s' % (
                    package_name,
                    'master',
            ))

    def get_svn_url(self, package_name):
        # what's the svn url?
        svn_url = None
        namespace = package_name.split('.')[0]
        # are there already packages checked out with same namespace?
        dirs = os.listdir('.')
        for dir in dirs:
            if dir.startswith('%s.' % namespace):
                try:
                    tmp_url = '/'.join(scm.get_package_root_url(dir).split('/')[:-1])
                    if tmp_url and '%s/' % package_name in svn.listdir(tmp_url):
                        svn_url = os.path.join(tmp_url, package_name, 'trunk')
                        print svn_url
                        break
                except scm.NotAScm:
                    pass
        if svn_url:
            print ' * found a package under %s' % svn_url
            msg = 'SVN project root url [%s]' % \
                    output.ColorString(svn_url, output.YELLOW_BOLD)
            def input_validator(v):
                if not v:
                    return True
                if not svn.isdir(v.strip()):
                    return 'URL not found'
                return True
            url_input = input.prompt(msg, input_validator)
            if url_input:
                svn_url = url_input.strip()
        else:
            msg = 'SVN project root url:'
            def input_validator(v):
                if not v or not svn.isdir(v.strip()):
                    return 'URL not found'
                return True
            url_input = input.prompt(msg, input_validator)
            svn_url = url_input.strip()
        # check svn layout
        if not svn.check_project_layout(svn_url, raise_exception=False):
            # we should have the folders trunk, tags, branches in the project
            output.error('Project does not have default layout with trunk, ' +\
                        'tags and branches. At least one folder is missing.',
                        exit=True)
        return svn_url

basecommand.registerCommand(CheckoutCommand)
