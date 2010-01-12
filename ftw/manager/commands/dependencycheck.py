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
    Der "dependencycheck" Befehl überprüft, ob in den Abhängigkeiten Packete
    angegeben sind, von denen es eine neue Version gibt oder ob Änderungen an den
    Packeten gemacht wurden.

    Anwendung

    * Wird der Befehl auf dem Root-Ordner des Packets ausgeführt, also z.B. im
      Ordner "trunk", so werden die im setup.py definierten Abhängigkeiten überprüft

    * Wird der Befehl auf einem Ordner ausgeführt, welches ausgecheckte Pakete
      enthält (z.B. der src-Ordner), so werden diese Pakete aufgelistet.

    * Die Resultate des Befehls werden gecacht. Mit dem optionalen Parametern
      --refresh (oder -r) kann bewirkt werden, dass alle Informationen neu abgefragt
      werden.

    * Mit dem Parameter --config (oder -c) kann ein buildout.cfg angegeben werden,
      welches dann nach version-pinnings durchsucht wird.
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
        self.parser.add_option('-v', '--verbose', dest='verbose',
                               action='store_true', default=False,
                               help='Print executed commands')

    def __call__(self):
        if self.options.verbose:
            from ftw.manager import utils
            utils.FORCE_LOG = True
        titles = (
            'Package',
            'Current Tag',
            'Newest Tag',
            'Untagged Changes',
            )
        table = output.ASCIITable(*titles)
        versions = self.package_versions
        force_reload = self.options.refresh
        for package, v in self.dependency_packages:
            warn = False
            ctag = package in versions.keys() and str(versions[package]) or ''
            info = scm.PackageInfoMemory().get_info(package,
                                                    force_reload=force_reload)
            ntag = info and str(info['newest_tag']) or ''
            if ntag and ctag:
                if ntag<ctag:
                    ntag = output.colorize(ntag, output.WARNING)
                    warn = True
                elif ntag>ctag:
                    ntag = output.colorize(ntag, output.ERROR)
                    warn = True
                elif ntag==ctag:
                    ntag = output.colorize(ntag, output.INFO)
            chg = ''
            if info and info['changes']:
                chg = output.colorize('YES', output.WARNING)
                warn = True
            table.push((
                    warn and output.colorize(package, output.WARNING) or package,
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
        if os.path.isfile('setup.py'):
            return distutils.core.run_setup('setup.py')
        else:
            return None

    @property
    @memoize
    def dependency_packages(self):
        dependencies = []
        if self.egg:
            for pkg in self.egg.install_requires:
                name = pkg.split('=')[0].split('<')[0].split('>')[0].strip()
                version = None
                if '=' in pkg:
                    version = pkg.split('=')[-1].strip()
                if name not in IGNORE_EGGS:
                    dependencies.append((name, version))
        else:
            # source directory ?
            for pkg in os.listdir('.'):
                path = os.path.abspath(pkg)
                if os.path.isdir(path) and scm.lazy_is_scm(path):
                    dependencies.append((pkg, None))
        return dependencies


basecommand.registerCommand(DependencyCheckCommand)
