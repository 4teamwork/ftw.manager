# -*- coding: utf8 -*-

import os

from ftw.manager.commands import basecommand
from ftw.manager.utils import output
from ftw.manager.utils import runcmd
from ftw.manager.utils import scm
from ftw.manager.utils.memoize import memoize

class FileSystemRootReached(Exception):
    pass

class I18NDudeBaseCommand(basecommand.BaseCommand):
    
    def check_conditions(self):
        output.part_title('Checking Conditions')
        # we should be in a buildout directory
        try:
            buildout_dir = self.buildout_dir
            print '  found buildout at:', buildout_dir
        except FileSystemRootReached:
            output.error('Could not find buildout directory. Run bin/buildout first', exit=1)
        # we should have a i18ndude executable in the bin folder
        if not os.path.exists(os.path.join(buildout_dir, 'bin', 'i18ndude')):
            output.error('Could not find i18ndude executable at %s' % \
                         os.path.join(buildout_dir, 'bin', 'i18ndude'), exit=1)
        self.i18ndude = os.path.join(buildout_dir, 'bin', 'i18ndude')
        # we should be in a local repository
        try:
            package_name = scm.get_package_name('.')
            print '  using package name:', package_name
        except scm.NotAScm:
            output.error('Not in a SVN- or GIT-Checkout, unable to guess package name', exit=1)
        # get package root
        package_root = scm.get_package_root_path('.')
        print '  using package root path:', package_root
        # check locales directory
        self.locales_dir = os.path.abspath(os.path.join(
                package_root,
                '/'.join(package_name.split('.')),
                'locales',
        ))
        if not os.path.isdir(self.locales_dir):
            runcmd('mkdir %s' % self.locales_dir)

    @property
    @memoize
    def buildout_dir(self):
        path = ['.']
        zopeFound = False
        instance = []
        while not zopeFound:
            dir = os.listdir('/'.join(path))
            if '/'==os.path.abspath('/'.join(path)):
                raise FileSystemRootReached
            elif 'bin' in dir:
                binContents = os.listdir('/'.join(path+['bin']))
                instances = filter(lambda x:x.startswith('instance') or x=='i18ndude', binContents)
                if len(instances)>0:
                    zopeFound = True
                else:
                    path.append('..')
            else:
                path.append('..')
        return os.path.abspath('/'.join(path))


class BuildPotCommand(I18NDudeBaseCommand):
    """
    Aktualisiert oder erstellt die .POT-Dateien eines Packets. Dieser Befehl
    wird in einem lokalen Checkout eines Eggs ausgeführt.

    Voraussetzungen:

    Der i18n-dude muss im Buildout eingetragen und installiert sein:
        [buildout]
        parts += i18ndude

        [i18ndude]
        recipe = zc.recipe.egg
        eggs = i18ndude
    """

    command_name = 'i18npot'
    command_shortcut = 'ib'
    description = 'Aktualisiert die i18n-POT-Dateien eines Packets'
    usage = 'ftw %s' % command_name

    def __call__(self):
        self.check_conditions()
        package_name = scm.get_package_name('.')
        package_root = scm.get_package_root_path('.')
        package_dir = os.path.join(package_root, *package_name.split('.'))
        pot_path = os.path.join(self.locales_dir, '%s.pot' % package_name)
        output.part_title('Rebuilding pot file at %s' % pot_path)
        # rebuild
        cmd = ['%s rebuild-pot' % self.i18ndude]
        cmd.append('--pot %s' % pot_path)
        # manual file
        manual_file = os.path.join(self.locales_dir, '%s-manual.pot' % package_name)
        if os.path.exists(manual_file):
            print '  merging manual pot file:', manual_file
            cmd.append('--merge %s' % manual_file)
        cmd.append('--create %s %s' % (
                scm.get_package_name('.'),
                package_dir,
        ))
        cmd = ' \\\n'.join(cmd)
        runcmd(cmd)

basecommand.registerCommand(BuildPotCommand)


class SyncPoCommand(I18NDudeBaseCommand):
    """
    Aktualisiert die Übersetzungs-Dateien (.po) einer bestimmten Sprache
    oder aller Sprachen.
    """
    command_name = 'i18nsync'
    command_shortcut = 'is'
    description = 'Aktualisiert die Übersetzungs-Dateien einer Sprache'
    usage = 'ftw %s [LANG-CODE]' % command_name

    def __call__(self):
        if len(self.args)<1:
            output.error('Language code is required', exit=1)
        lang = self.args[0]
        # check
        self.check_conditions()
        package_name = scm.get_package_name('.')
        # check pot file
        pot_path = os.path.join(self.locales_dir, '%s.pot' % package_name)
        if not os.path.exists(pot_path):
            output.error('Could not find pot file at: %s' % pot_path, exit=1)
        # check language directory
        lang_dir = os.path.join(self.locales_dir, lang, 'LC_MESSAGES')
        if not os.path.isdir(lang_dir):
            runcmd('mkdir -p %s' % lang_dir)
        # touch po file
        po_file = os.path.join(lang_dir, '%s.po' % package_name)
        if not os.path.isfile(po_file):
            runcmd('touch %s' % po_file)
        # sync
        output.part_title('Syncing language "%s"' % lang)
        cmd = '%s sync --pot %s %s' % (
                self.i18ndude,
                pot_path,
                po_file,
        )
        runcmd(cmd)
        # remove language
        output.part_title('Removing language code from po file')
        data = open(po_file).read().split('\n')
        file = open(po_file, 'w')
        for row in data:
            if not row.startswith('"Language-Code') and not row.startswith('"Language-Name'):
                file.write(row)
                file.write('\n')
        file.close()


basecommand.registerCommand(SyncPoCommand)

