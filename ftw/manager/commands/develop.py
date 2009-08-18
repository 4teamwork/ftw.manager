
import os
from ftw.manager.commands import basecommand
from ftw.manager.utils import runcmd
from ftw.manager.utils import output
from ftw.manager.utils import input
from ftw.manager.utils import scm

class DevelopCommand(basecommand.BaseCommand):
        """
        Sets a package to develop.
        This Command is run at the root of the package you
        want to set to develop.

        main_package:   You can define a package wich has a dependency
                        to this package with version pinning. The
                        version pinning will be removed.
        """

        command_name = 'develop'
        command_shortcut = 'dev'
        description = 'Sets a package to develop'
        usage = '%prog %s [main_package] [options]'

        def __call__(self):
            self.check_conditions()
            self.remove_egg()
            self.set_to_develop()
            if len(self.args):
                self.fix_dependency(self.args[0])
        
        def check_conditions(self):
            output.part_title('Checking conditions')
            if not scm.is_subversion('.') and not scm.is_git('.'):
                # without subversion it doesnt work...
                output.error('Not in a local repository', exit=True)
            svn_url = scm.get_svn_url('.')
            if max([int(x in svn_url) for x in ['trunk', 'tags', 'branches']])==0:
                # command must be run at the "trunk" folder of a package
                output.error('Please run this command at the root of the package' +\
                             '(trunk folder, branch, tag)', exit=True)
            for file in ['../../buildout.cfg']:
                if not os.path.isfile(file):
                    output.error('Could not find the file %s' % file, exit=True)
            if os.path.abspath('.').split('/')[-2]!='src':
                output.error('I\'m confused: can\'t find a "src" folder...', exit=True)
            if len(self.args):
                main_package = self.args[0]
                package_name = scm.get_package_name('.')
                path = os.path.join('../%s' % main_package)
                if not os.path.isdir(path):
                    output.error('Can\'t find main_package (%s) at %s' % (
                            main_package,
                            path,
                    ), exit=True)
                dependency_file = os.path.join(path, 'dependencies.txt')
                if not os.path.isfile(dependency_file):
                    output.error('Can\'t find depedency file at %s' % (
                            dependency_file,
                    ))
                    input.prompt('Are you shure that %s is your main package and has a dependency to %s?' % (
                            main_package,
                            package_name,
                    ))

        def remove_egg(self):
            package_name = scm.get_package_name('.')
            output.part_title('Removing eggs')
            runcmd('rm -rf ../../eggs/%s*' % package_name)
                

        def set_to_develop(self):
            package_name = scm.get_package_name('.')
            output.part_title('Setting %s to develop in buildout.cfg' % package_name)
            buildout_file = '../../buildout.cfg'
            buildout = open(buildout_file).read().split('\n')
            new_buildout = []
            for row in buildout:
                new_buildout.append(row)
                if row.strip().startswith('develop'):
                    new_buildout.append('    src/%s' % package_name)
            f = open(buildout_file, 'w')
            f.write('\n'.join(new_buildout))
            f.close()

        def fix_dependency(self, main_package):
            output.part_title('Fixing dependency in %s' % main_package)
            package_name = scm.get_package_name('.')
            path = os.path.join('../%s' % main_package)
            runcmd('echo "%s" >> %s/develop.txt' % (
                package_name,
                path
            ))


basecommand.registerCommand(DevelopCommand)


