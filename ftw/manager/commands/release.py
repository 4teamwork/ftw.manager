# -*- coding: utf8 -*-

import os
import sys
import ConfigParser

from ftw.manager import utils
from ftw.manager.commands import basecommand
from ftw.manager.utils import output
from ftw.manager.utils import input
from ftw.manager.utils import runcmd
from ftw.manager.utils import subversion as svn
from ftw.manager.utils.memoize import memoize

class ReleaseCommand(basecommand.BaseCommand):
    u"""
    Der "release" command publiziert die aktuellen Änderungen eines Packets in
    einer neuen Version. Der Befehl sollte vom root-Verzeichnis eines SVN-Checkouts
    (trunk) ausgeführt werden.
    Als ausgangslage wird der Versionsname verwendet, der im setup.py eingetragen
    ist (z.B. wenn "2.0.1-dev" im setup.py steht wird eine neue Version "2.0.1"
    erstellt).

    Es werden folgende Schritte gemacht:
        * Es wird ein SVN-Tag erstellt
        * Die Version im Trunk wird erhöht (version.txt und HISTORY.txt)
        * Die Version im Tag wird angepasst (version.txt und HISTORY.txt)
        * Der Tag wird aufgeräumt (setup.cfg : dev-angaben entfernen)
        * Vom Tag wird ein Egg erstellt und ins pypi geladen
    """

    command_name = 'release'
    command_shortcut = 'rl'
    description = 'Release eines Packets erstellen'

    def register_options(self):
        """
        self.parser.add_option('-d', '--dry-run', dest='dryrun',
                               action='store_true',
                               help=u'Keine Änderungen vornehmen')
        """
        self.parser.add_option('-E', '--no-egg', dest='release_egg',
                               action='store_false',
                               help=u'Kein Egg erstellen')

    def __call__(self):
        self.analyse()
        if not self.options.release_egg:
            self.check_pyprc()
        self.check_versions()

    def analyse(self):
        if not svn.is_subversion('.'):
            # without subversion it doesnt work...
            output.error('Not in a subversion checkout', exit=True)
        if not svn.check_project_layout('.', raise_exception=False):
            # we should have the folders trunk, tags, branches in the project
            output.error('Project does not have default layout with trunk, ' +\
                        'tags and branches. At least one folder is missing.',
                        exit=True)
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

    def check_versions(self):
        version_file = os.path.join(svn.get_package_name('.').replace('.', '/'),
                                    'version.txt')
        trunk_version = open(version_file).read().strip()
        print 'Trunk-Version:       %s' % output.ColorString(trunk_version,
                                                             output.YELLOW)
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
        print 'Tagging Version:     %s' % output.ColorString(next_version,
                                                             output.YELLOW)
        print 'Setting trunk to:    %s' % output.ColorString(next_trunk_version,
                                                             output.YELLOW)
        self.new_tag_version = next_version
        self.new_trunk_version = next_trunk_version

    def bump_version_proposal(self, version):
        version_parts = version.split('-')
        version = version_parts[0].split('.')
        version[-1] = str(int(version[-1])+1)
        version_parts[0] = '.'.join(version)
        return '-'.join(version_parts)

    def check_pyprc(self):
        pypirc_path = os.path.expanduser('~/.pypirc')
        if not os.path.isfile(pypirc_path):
            # ~/.pypirc required
            output.error('Could not find the file %s' % pypirc_path, exit=True)
        config = ConfigParser.ConfigParser()
        config.readfp(open(pypirc_path))
        basic_namespace = svn.get_package_name('.').split('.')[0]
        print 'Checking .pypirc for egg-release targets'
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


basecommand.registerCommand(ReleaseCommand)
