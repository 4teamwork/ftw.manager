# -*- coding: utf8 -*-

import os
import sys
import ConfigParser

from ftw.manager import utils
from ftw.manager.commands import basecommand
from ftw.manager.utils import *
from ftw.manager.utils import output
from ftw.manager.utils import input
from ftw.manager.utils import subversion as svn
from ftw.manager.utils.memoize import memoize

class ReleaseCommand(basecommand.BaseCommand):
    """
    Der "release" command publiziert die aktuellen Änderungen eines Packets in
    einer neuen Version. Der Befehl sollte vom root-Verzeichnis eines SVN-Checkouts
    (trunk) ausgeführt werden.

    Bedingungen
    -----------
    *   Die Option *long_description* im *setup.py* muss validierter restructuredText
        sein
    *   Man muss sich im Root-Verzeichnis eines SVN-Checkouts befinden: Wenn nur
        das Egg erstellt (-e) wird, kann dies der trunk, ein branch oder ein tag
        sein, ansonsten muss es der trunk sein.
    *   Das Projekt muss ein gültiges SVN-Layout haben, d.H. die Ordner trunk,
        branches und tags besitzen
    *   Die Dateien setup.py und setup.cfg sind im aktuellen Ordner notwendig
    *   Die Version ist in der Datei my/package/version.txt gespeichert
    *   Eine Datei docs/HISTORY.txt ist notwendig
    *   Das lokale Repository darf keine Änderungen haben, die nicht commitet wurden

    Aktionen
    --------
    *   Es wird ein SVN-Tag erstellt
    *   Die Version im Trunk wird erhöht (version.txt und HISTORY.txt)
    *   Die Version im Tag wird angepasst (version.txt und HISTORY.txt)
    *   Der Tag wird aufgeräumt (setup.cfg : dev-angaben entfernen)
    *   Vom Tag wird ein Egg erstellt und ins pypi geladen
    """

    command_name = 'release'
    command_shortcut = 'rl'
    description = 'Release eines Packets erstellen'

    def register_options(self):
        self.parser.add_option('-e', '--only-egg', dest='release_egg_only',
                               action='store_true', default=False,
                               help=u'Nur Egg erstellen, kein SVN-Tag machen')
        self.parser.add_option('-E', '--no-egg', dest='release_egg',
                               action='store_false', default=True,
                               help=u'Kein Egg erstellen')
        self.parser.add_option('-i', '--ignore-doc-errors', dest='ignore_doc_errors',
                               action='store_true', default=False,
                               help=u'Docstring Fehler (reStructuredText) ignorieren')

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
            self.switch_to_trunk()
        # swith back to trunk

    def analyse(self):
        output.part_title('Checking subversion project')
        if not svn.is_subversion('.'):
            # without subversion it doesnt work...
            output.error('Not in a subversion checkout', exit=True)
        if not svn.check_project_layout('.', raise_exception=False):
            # we should have the folders trunk, tags, branches in the project
            output.error('Project does not have default layout with trunk, ' +\
                        'tags and branches. At least one folder is missing.',
                        exit=True)
        if not self.options.release_egg_only:
            if svn.get_svn_url('.')!=svn.get_package_root_url('.')+'/trunk':
                # command must be run at the "trunk" folder of a package
                output.error('Please run this command at the root of the package' +\
                             '(trunk folder)', exit=True)
        if not os.path.isfile('setup.py'):
            # setup.py is required
            output.error('Could not find the file ./setup.py', exit=True)
        if not os.path.isfile('setup.cfg'):
            # setup.cfg is required
            output.error('Could not find the file ./setup.cfg', exit=True)
        if not os.path.isfile('docs/HISTORY.txt'):
            # docs/HISTORY.txt is required
            output.error('Could not find the file ./docs/HISTORY.txt', exit=True)
        version_file = os.path.join(svn.get_package_name('.').replace('.', '/'),
                                    'version.txt')
        if not os.path.isfile(version_file):
            # version.txt is required
            output.error('Could not find the file %s' % version_file, exit=True)
        # check subversion state
        cmd = 'svn st | grep -v ^X | grep -v ^Performing | grep -v ^$'
        if len(runcmd(cmd, log=False, respond=True)):
            output.error('You have local changes, please commit them first.',
                         exit=True)

    def check_doc(self):
        if self.options.ignore_doc_errors:
            return
        output.part_title('Checking setup.py docstring (restructuredtext)')
        cmd = '%s setup.py check --restructuredtext --strict' % sys.executable
        if runcmd_with_exitcode(cmd, log=0)!=0:
            output.error('You have errors in your docstring (README.txt, HISTORY.txt, ...)', exit=1)

    def check_versions(self):
        output.part_title('Checking package versions')
        version_file = os.path.join(svn.get_package_name('.').replace('.', '/'),
                                    'version.txt')
        trunk_version = open(version_file).read().strip()
        print ' * Current version of trunk:         %s' %\
                output.ColorString(trunk_version, output.YELLOW)
        next_version = trunk_version.split('-')[0]
        existing_tags = svn.get_existing_tags('.')
        if next_version in existing_tags.keys():
            output.warning('Tag %s already existing' % next_version)
        # ask for next tag version
        prompt_msg = 'Which version do you want to release now? [%s]' % \
                        output.ColorString(next_version, output.YELLOW_BOLD)
        next_version_input = input.prompt(prompt_msg, lambda v:v in existing_tags.keys() and 'Tag already existing' or True)
        if next_version_input:
            next_version = next_version_input
        # ask for next trunk version
        next_trunk_version = next_version + '-dev'
        next_trunk_version = self.bump_version_proposal(next_trunk_version)
        prompt_msg = 'Which version should trunk have afterwards? [%s]' % \
                        output.ColorString(next_trunk_version, output.YELLOW_BOLD)
        next_trunk_version_input = input.prompt(prompt_msg)
        if next_trunk_version_input:
            next_trunk_version = next_trunk_version_input
        print ' * The version of the tag will be:   %s' %\
                output.ColorString(next_version, output.YELLOW)
        print ' * New version of the trunk will be: %s' %\
                output.ColorString(next_trunk_version, output.YELLOW)
        self.new_tag_version = next_version
        self.new_trunk_version = next_trunk_version

    def bump_version_proposal(self, version):
        version_parts = version.split('-')
        version = version_parts[0].split('.')
        version[-1] = str(int(version[-1])+1)
        version_parts[0] = '.'.join(version)
        return '-'.join(version_parts)

    def check_pyprc(self):
        output.part_title('Checking .pypirc for egg-release targets')
        pypirc_path = os.path.expanduser('~/.pypirc')
        if not os.path.isfile(pypirc_path):
            # ~/.pypirc required
            output.error('Could not find the file %s' % pypirc_path, exit=True)
        config = ConfigParser.ConfigParser()
        config.readfp(open(pypirc_path))
        basic_namespace = svn.get_package_name('.').split('.')[0]
        for section in config.sections():
            print '* found target "%s"' % output.ColorString(section,
                                            output.YELLOW)
        if basic_namespace in config.sections():
            self.pypi_target = basic_namespace
        else:
            self.pypi_target = config.sections()[0]
        msg = 'Please specify a pypi target for the egg relase [%s]' % \
                     output.ColorString(self.pypi_target, output.YELLOW_BOLD)
        pypi_target_input = input.prompt(msg, lambda v:\
                            not v or v in config.sections()
                            and True or 'Please select a target listed above')
        if pypi_target_input:
            self.pypi_target = pypi_target_input

    def create_tag(self):
        output.part_title('Creating subversion tag')
        root_url = svn.get_package_root_url('.')
        trunk_url = os.path.join(root_url, 'trunk')
        tag_url = os.path.join(root_url, 'tags', self.new_tag_version)
        cmd = 'svn cp %s %s -m "creating tag %s for package %s"' % (
            trunk_url,
            tag_url,
            self.new_tag_version,
            svn.get_package_name('.'),
        )
        runcmd(cmd)

    def bump_trunk_after_tagging(self):
        output.part_title('Bumping versions in trunk')
        version_file = os.path.join(svn.get_package_name('.').replace('.', '/'),
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
        cmd = 'svn ci -m "bumping versions in trunk of %s after tagging %s"' % (
                svn.get_package_name('.'),
                self.new_tag_version,
        )
        runcmd(cmd)

    def bump_tag_after_tagging(self):
        tag_url = os.path.join(svn.get_package_root_url('.'), 'tags',
                               self.new_tag_version)
        cmd = 'svn switch %s' % tag_url
        runcmd(cmd)
        output.part_title('Bumping versions in tag')
        version_file = os.path.join(svn.get_package_name('.').replace('.', '/'),
                                    'version.txt')
        print '* updating %s' % version_file
        version_txt = open(version_file, 'w')
        version_txt.write(self.new_tag_version)
        version_txt.close()
        print '* updating setup.cfg : removing dev stuff'
        data = open('setup.cfg').read().split('\n')
        file = open('setup.cfg', 'w')
        for line in data:
            if not line.startswith('tag_build') and not line.startswith('tag_svn_rev'):
                file.write(line)
        file.write('\n')
        file.close()
        cmd = 'svn ci -m "bumping versions in tag of %s after tagging %s"' % (
                svn.get_package_name('.'),
                self.new_tag_version,
        )
        runcmd(cmd)

    def release_egg(self):
        output.part_title('Releasing agg to target %s' % self.pypi_target)
        cmd = '%s setup.py mregister sdist bdist_egg mupload -r %s' % (
              sys.executable,
              self.pypi_target
        )
        runcmd(cmd)
        runcmd('rm -rf dist build')

    def switch_to_trunk(self):
        output.part_title('Cleaning up local repository')
        tag_url = os.path.join(svn.get_package_root_url('.'), 'trunk')
        cmd = 'svn switch %s' % tag_url
        runcmd(cmd)




basecommand.registerCommand(ReleaseCommand)
