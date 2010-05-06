# -*- coding: utf8 -*-

from ftw.manager.commands import basecommand
from ftw.manager.utils import git
from ftw.manager.utils import input
from ftw.manager.utils import output
from ftw.manager.utils import runcmd
from ftw.manager.utils import runcmd_with_exitcode
from ftw.manager.utils import scm
from ftw.manager.utils import subversion as svn
import ConfigParser
import os
import sys

class ReleaseCommand(basecommand.BaseCommand):
    """
    Der "release" command publiziert die aktuellen Änderungen eines Packets in
    einer neuen Version. Der Befehl sollte vom root-Verzeichnis eines SVN-Checkouts
    (trunk) ausgeführt werden.

    Bedingungen

    *   Die Option *long_description* im *setup.py* muss validierter restructuredText sein
    *   Man muss sich im Root-Verzeichnis eines SVN-Checkouts befinden: Wenn nur
        das Egg erstellt (-e) wird, kann dies der trunk, ein branch oder ein tag
        sein, ansonsten muss es der trunk sein.
    *   Das Projekt muss ein gültiges SVN-Layout haben, d.H. die Ordner trunk,
        branches und tags besitzen
    *   Die Dateien setup.py und setup.cfg sind im aktuellen Ordner notwendig
    *   Die Version ist in der Datei my/package/version.txt gespeichert
    *   Eine Datei docs/HISTORY.txt ist notwendig
    *   Das lokale Repository darf keine Änderungen haben, die nicht commitet wurden
    *   Es wird eine MANIFEST.in Datei erwartet. Existiert keine, wird eine angelegt.

    Aktionen

    *   Es wird ein SVN-Tag erstellt
    *   Die Version im Trunk wird erhöht (version.txt und HISTORY.txt)
    *   Die Version im Tag wird angepasst (version.txt und HISTORY.txt)
    *   Der Tag wird aufgeräumt (setup.cfg : dev-angaben entfernen)
    *   Vom Tag wird ein Egg erstellt und ins pypi geladen
    """

    command_name = 'release'
    command_shortcut = 'rl'
    description = 'Release eines Packets erstellen'
    usage = 'ftw %s [OPTIONS]' % command_name

    def register_options(self):
        self.parser.add_option('-e', '--only-egg', dest='release_egg_only',
                               action='store_true', default=False,
                               help='Nur Egg erstellen, kein SVN-Tag machen')
        self.parser.add_option('-E', '--no-egg', dest='release_egg',
                               action='store_false', default=True,
                               help='Kein Egg erstellen')
        self.parser.add_option('-i', '--ignore-doc-errors', dest='ignore_doc_errors',
                               action='store_true', default=False,
                               help='Docstring Fehler (reStructuredText) ignorieren')

    def __call__(self):
        self.check_doc()
        self.analyse()
        if self.options.release_egg:
            self.check_pyprc()
        if not self.options.release_egg_only:
            self.check_versions()
        print ''
        input.prompt('Are you sure to continue? [OK]')
        if not self.options.release_egg_only:
            self.create_tag()
            self.bump_trunk_after_tagging()
            self.bump_tag_after_tagging()
        if self.options.release_egg:
            self.release_egg()
        if not self.options.release_egg_only:
            self.switch_to_back()
        # swith back to trunk

    def analyse(self):
        output.part_title('Checking subversion project')
        if not scm.is_scm('.'):
            # without subversion or gitsvn it doesnt work...
            output.error('Current directory is not a subversion checkout, nor a git-svn repo',
                         exit=True)
        if scm.is_git('.'):
            git.pull_changes('.')
            git.push_committed_changes('.')
        root_svn = scm.get_package_root_url('.')
        if not svn.check_project_layout(root_svn, raise_exception=False,
                                        ask_for_creation=False):
            # we should have the folders trunk, tags, branches in the project
            output.error('Project does not have default layout with trunk, ' +\
                             'tags and branches. At least one folder is missing.',
                         exit=True)
        if not self.options.release_egg_only:
            if scm.get_svn_url('.') not in (scm.get_package_root_url('.')+'/trunk',
                                        scm.get_package_root_url('.')+'/branches',):
                # command must be run at the "trunk" folder of a package
                output.error('Please run this command at the root of the package ' +\
                                 '(trunk/branch folder)', exit=True)
        if not os.path.isfile('setup.py'):
            # setup.py is required
            output.error('Could not find the file ./setup.py', exit=True)
        if not os.path.isfile('docs/HISTORY.txt'):
            # docs/HISTORY.txt is required
            output.error('Could not find the file ./docs/HISTORY.txt', exit=True)
        version_file = os.path.join(scm.get_package_name('.').replace('.', '/'),
                                    'version.txt')
        if not os.path.isfile(version_file):
            # version.txt is required
            output.error('Could not find the file %s' % version_file, exit=True)
        if not self.options.release_egg_only and not os.path.isfile('MANIFEST.in'):
            output.warning('Could not find the file ./MANIFEST.in, creating one')
            f = open('MANIFEST.in', 'w')
            namespace = scm.get_package_name('.').split('.')[0]
            f.write('recursive-include %s *\n' % namespace)
            f.write('global-exclude *pyc\n')
            f.close()
            print 'created MANIFEST.in with following content:'
            print '-' * 30
            print output.colorize(open('MANIFEST.in').read(), output.INFO)
            print '-' * 30
            if input.prompt_bool('Would you like to commit the MANIFEST.in?'):
                if scm.is_subversion('.'):
                    runcmd('svn add MANIFEST.in')
                    runcmd('svn commit -m "added MANIFEST.in for %s"' %
                           scm.get_package_name('.'))
                elif scm.is_git('.'):
                    runcmd('git add MANIFEST.in')
                    runcmd('git commit -am "added MANIFEST.in for %s"' %
                           scm.get_package_name('.'))
                    runcmd('git svn dcommit')
        # check subversion state
        if scm.has_local_changes('.'):
            output.error('You have local changes, please commit them first.',
                         exit=True)

    def check_doc(self):
        if self.options.ignore_doc_errors:
            return
        output.part_title('Checking setup.py docstring (restructuredtext)')
        cmd = '%s setup.py check --restructuredtext --strict' % sys.executable
        if runcmd_with_exitcode(cmd, log=0)!=0:
            output.error('You have errors in your docstring (README.txt, HISTORY.txt, ...)'+\
                             '\nRun "ftw checkdocs" for more details.', exit=1)

    def check_versions(self):
        output.part_title('Checking package versions')
        version_file = os.path.join(scm.get_package_name('.').replace('.', '/'),
                                    'version.txt')
        trunk_version = open(version_file).read().strip()
        print ' * Current version of trunk:         %s' %\
            output.colorize(trunk_version, output.WARNING)
        next_version = trunk_version.split('-')[0]
        root_svn = scm.get_package_root_url('.')
        existing_tags = svn.get_existing_tags(root_svn)
        if next_version in existing_tags.keys():
            output.warning('Tag %s already existing' % next_version)
        # ask for next tag version
        prompt_msg = 'Which version do you want to release now? [%s]' % \
            output.colorize(next_version, output.BOLD_WARNING)
        next_version_input = input.prompt(prompt_msg, lambda v:v in existing_tags.keys() and 'Tag already existing' or True)
        if next_version_input:
            next_version = next_version_input
        # ask for next trunk version
        next_trunk_version = next_version + '-dev'
        next_trunk_version = self.bump_version_proposal(next_trunk_version)
        prompt_msg = 'Which version should trunk have afterwards? [%s]' % \
            output.colorize(next_trunk_version, output.BOLD_WARNING)
        next_trunk_version_input = input.prompt(prompt_msg)
        if next_trunk_version_input:
            next_trunk_version = next_trunk_version_input
        print ' * The version of the tag will be:   %s' %\
            output.colorize(next_version, output.WARNING)
        print ' * New version of the trunk will be: %s' %\
            output.colorize(next_trunk_version, output.WARNING)
        self.new_tag_version = next_version
        self.new_trunk_version = next_trunk_version

    def bump_version_proposal(self, version):
        try:
            version_parts = version.split('-')
            version = version_parts[0].split('.')
            last_num = version[-1]
            # increase
            try:
                last_num = str( int( last_num ) + 1 )
            except ValueError:
                last_num_pos = last_num[-1]
                last_num_pos = str( int( last_num_pos ) + 1 )
                last_num = last_num[:-1] + last_num_pos
            # .. use
            version[-1] = last_num
            version_parts[0] = '.'.join(version)
            return '-'.join(version_parts)
        except ValueError:
            return '-- no proposal --'

    def check_pyprc(self):
        output.part_title('Checking .pypirc for egg-release targets')
        pypirc_path = os.path.expanduser('~/.pypirc')
        if not os.path.isfile(pypirc_path):
            # ~/.pypirc required
            output.error('Could not find the file %s' % pypirc_path, exit=True)
        config = ConfigParser.ConfigParser()
        config.readfp(open(pypirc_path))
        basic_namespace = scm.get_package_name('.').split('.')[0]
        for section in config.sections():
            print '* found target "%s"' % output.colorize(section,
                                                          output.WARNING)
        if basic_namespace in config.sections():
            self.pypi_target = basic_namespace
        else:
            self.pypi_target = ''
        msg = 'Please specify a pypi target for the egg relase [%s]' % \
            output.colorize(self.pypi_target, output.BOLD_WARNING)
        pypi_target_input = input.prompt(msg, lambda v:\
                                             (self.pypi_target and not v) or v in
                                         config.sections()
                                         and True or 'Please select a target listed above')
        if pypi_target_input:
            self.pypi_target = pypi_target_input

    def create_tag(self):
        output.part_title('Creating subversion tag')
        if scm.is_subversion('.'):
            root_url = scm.get_package_root_url('.')
            trunk_url = scm.get_svn_url('.')
            tag_url = os.path.join(root_url, 'tags', self.new_tag_version)
            cmd = 'svn cp %s %s -m "creating tag %s for package %s"' % (
                trunk_url,
                tag_url,
                self.new_tag_version,
                svn.get_package_name('.'),
                )
            runcmd(cmd)
        elif scm.is_git('.'):
            cmd = 'git svn tag %s' % self.new_tag_version
            runcmd(cmd)
            git.pull_changes('.')

    def bump_trunk_after_tagging(self):
        output.part_title('Bumping versions in trunk')
        version_file = os.path.join(scm.get_package_name('.').replace('.', '/'),
                                    'version.txt')
        print '* updating %s' % version_file
        version_txt = open(version_file, 'w')
        version_txt.write(self.new_trunk_version)
        version_txt.close()
        history_file = 'docs/HISTORY.txt'
        print '* updating %s' % history_file
        insert_title_on_line = 3
        version = self.new_trunk_version.split('-')[0]
        data = open(history_file).read().split('\n')
        data = data[:insert_title_on_line] +\
            ['', version,'-' * len(version), '', ] +\
            data[insert_title_on_line:]
        file = open(history_file, 'w')
        file.write('\n'.join(data))
        file.close()
        ci_msg = 'bumping versions in trunk of %s after tagging %s' % (
            scm.get_package_name('.'),
            self.new_tag_version,
            )
        if scm.is_subversion('.'):
            cmd = 'svn ci -m "%s"' % ci_msg
            runcmd(cmd)
        elif scm.is_git('.'):
            cmd = 'git commit -a -m "%s"' % ci_msg
            runcmd(cmd)
            git.push_committed_changes('.')

    def bump_tag_after_tagging(self):
        self._package_root = scm.get_package_root_url('.')
        self._checkout_url = scm.get_svn_url('.')
        if scm.is_subversion('.'):
            tag_url = os.path.join(scm.get_package_root_url('.'), 'tags',
                                   self.new_tag_version)
            cmd = 'svn switch %s' % tag_url
            runcmd(cmd)
        elif scm.is_git('.'):
            cmd = 'git checkout remotes/tags/%s; git checkout -b %s' % (
                self.new_tag_version,
                self.new_tag_version
                )
            runcmd(cmd)
        output.part_title('Bumping versions in tag')
        version_file = os.path.join(scm.get_package_name('.').replace('.', '/'),
                                    'version.txt')
        print '* updating %s' % version_file
        version_txt = open(version_file, 'w')
        version_txt.write(self.new_tag_version)
        version_txt.close()
        if os.path.isfile('setup.cfg'):
            print '* updating setup.cfg : removing dev stuff'
            data = open('setup.cfg').read().split('\n')
            file = open('setup.cfg', 'w')
            for line in data:
                if not line.startswith('tag_build') and not line.startswith('tag_svn_rev'):
                    file.write(line)
                    file.write('\n')
            file.write('\n')
            file.close()
        ci_msg = "bumping versions in tag of %s after tagging %s"  % (
            scm.get_package_name('.'),
            self.new_tag_version,
            )
        if scm.is_subversion('.'):
            cmd = 'svn ci -m "%s"' % ci_msg
            runcmd(cmd)
        elif scm.is_git('.'):
            cmd = 'git commit -a -m "%s" ; git svn dcommit' % ci_msg
            runcmd(cmd)

    def release_egg(self):
        output.part_title('Releasing agg to target %s' % self.pypi_target)
        cmd = '%s setup.py mregister sdist bdist_egg mupload -r %s' % (
            sys.executable,
            self.pypi_target
            )
        runcmd(cmd)
        runcmd('rm -rf dist build')

    def switch_to_back(self):
        output.part_title('Cleaning up local repository')
        if scm.is_subversion('.'):
            cmd = 'svn switch %s' % self._checkout_url
            runcmd(cmd)
        elif scm.is_git('.'):
            git.push_committed_changes('.')
            folder = self._checkout_url[len(self._package_root)+1:]
            if folder=='trunk':
                folder = 'master'
            elif folder.startswith('branches'):
                folder = 'remotes/%s' % folder[len('branches/'):]
            else:
                folder = 'remotes/%s' % folder
            cmd = 'git checkout %s' % folder
            cmd += ' ; git branch -D %s' % self.new_tag_version
            runcmd(cmd)



basecommand.registerCommand(ReleaseCommand)
