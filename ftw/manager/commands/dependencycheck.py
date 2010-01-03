# -*- coding: utf-8 -*-

import os
import distutils.core
import ConfigParser

from ftw.manager.commands import basecommand
from ftw.manager.utils.memoize import memoize
from ftw.manager.utils import scm
from ftw.manager.utils import output

IGNORE_EGGS = [
    'setuptools',
    'Plone',
    ]

class DependencyCheckCommand(basecommand.BaseCommand):
    """
    Der "dependencycheck" Befehl überprüft, ob in den Abhängigkeiten Packete angegeben sind,
    von denen es eine neue Version gibt oder ob Änderungen an den Packeten gemacht wurden.

    Anwendung:

    * Der Befehl muss auf dem Root-Ordner des Packets ausgeführt werden (also z.B. im "trunk"
    ordner).
    * Die Resultate des Befehls werden gecacht. Mit optionalen Parametern kann bewirkt werden,
    dass alle Informationen neu abgefragt werden.
    """

    command_name = 'dependencycheck'
    command_shortcut = 'dc'
    description = 'Überprüfen der Abhängigkeiten'
    usage = 'ftw %s [OPTIONS]' % command_name

    def register_options(self):
        self.parser.add_option('-r', '--refresh', dest='refresh',
                               action='store_true', default=False,
                               help='Force refresh. Recalculates all infos')
        self.parser.add_option('-c', '--config', dest='buildout',
                               action='store', default=None,
                               help='Buildout config file containing version infos')

    def __call__(self):
        titles = (
            'Package',
            'Current Tag',
            'Newest Tag',
            'Untagged Changes',
            )
        table = output.ASCIITable(*titles)
        versions = self.package_versions
        for package, v in self.dependency_packages:
            ctag = package in versions.keys() and str(versions[package]) or ''
            info = scm.PackageInfoMemory().get_info(package)
            ntag = info and str(info['newest_tag']) or ''
            chg = info and str(info['changes']) and 'YES' or ''
            table.push((
                    package,
                    ctag,
                    ntag,
                    chg,
                    ))
        table()
        
    @property
    @memoize
    def package_versions(self):
        """ Returns a dictionary of packages and version pins
        """
        # -- pinned in the dependencies
        pins = {}
        for pkg, version in self.dependency_packages:
            if version and pkg not in pins.keys():
                pins[pkg] = version
        # -- pinnend in the buildout config
        if self.options.buildout:
            parser = ConfigParser.SafeConfigParser()
            loaded = [self.options.buildout]
            # load extends
            def load_extends(file, dir):
                path = os.path.join(dir, file)
                if path in loaded or file.startswith('http'):
                    return
                loaded.append(path)
                parser.read(path)
                if parser.has_option('buildout', 'extends'):
                    for file in parser.get('buildout', 'extends').split():
                        load_extends(file, os.path.dirname(path))
            load_extends(os.path.basename(self.options.buildout),
                         os.path.abspath(os.path.dirname(self.options.buildout)))
            # -- add versions
            if parser.has_option('buildout', 'versions'):
                version_section_name = parser.get('buildout', 'versions')
                for pkg, version in parser.items(version_section_name):
                    pins[pkg] = version
        return pins

    @property
    @memoize
    def egg(self):
        return distutils.core.run_setup('setup.py')

    @property
    @memoize
    def dependency_packages(self):
        dependencies = []
        for pkg in self.egg.install_requires:
            name = pkg.split('=')[0].split('<')[0].split('>')[0].strip()
            version = None
            if '=' in pkg:
                version = pkg.split('=')[-1].strip()
            if name not in IGNORE_EGGS:
                dependencies.append((name, version))
        return dependencies


basecommand.registerCommand(DependencyCheckCommand)
