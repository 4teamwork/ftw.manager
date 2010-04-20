# -*- coding: utf-8 -*-

import os
import re
import distutils.core
import ConfigParser
import tempfile
import urllib2

from ftw.manager.commands import basecommand
from ftw.manager.utils.memoize import memoize
from ftw.manager.utils import aggressive_decode
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

    * Wenn die Option --history verwendet wird, werden aus den aktualiserten Paketen
      die Änderungen im Format einer globalen HISTORY.txt-Datei zusammengeführt. Es
      werden nur Pakete beachtet, die in einer neuen Version als die verwendete
      existieren. Dazu sollte die Option --config immer verwendet werden.
      Wenn die Option --dev verwendent wird, werden alle Pakete aufgelistet, die nicht
      getaggte Änderungen im trunk haben.
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
        self.parser.add_option('-H', '--history', dest='history',
                               action='store_true', default=False,
                               help='Generate history file with all packages with a new ' +\
                                   'version')
        self.parser.add_option('-d', '--dev', dest='history_dev',
                               action='store_true', default=False,
                               help='List packages with modified trunk when using ' +\
                                   '--history option')

    def __call__(self):
        try:
            if self.options.verbose:
                from ftw.manager import utils
                utils.FORCE_LOG = True
            if self.options.history:
                self.print_history()
            else:
                self.print_table()
        finally:
            self.delete_downloaded_files()

    def print_table(self):
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

    def print_history(self):
        versions = self.package_versions
        force_reload = self.options.refresh
        packages_data = {}
        list_trunk_modifications = self.options.history_dev
        for package, v in self.dependency_packages:
            if self.options.verbose:
                print package
            ctag = package in versions.keys() and str(versions[package]) or ''
            info = scm.PackageInfoMemory().get_info(package,
                                                    force_reload=force_reload, prompt=False)
            ntag = info and str(info['newest_tag']) or ''
            if list_trunk_modifications and info and info['changes']:
                history = scm.PackageInfoMemory().get_history_for(package, 'trunk',
                                                                  prompt=False)
                if not history:
                    continue
                history = history.strip().split('\n')
                if ctag not in history:
                    print '* ERROR in', package, ': could not find tag', ctag, \
                        'in changelog'
                    continue
                packages_data[package] = history[2:history.index(ctag)]
            elif ntag and ctag and ntag!=ctag:
                history = scm.PackageInfoMemory().get_history_for(package,
                                                                  ntag, prompt=False)
                if not history:
                    continue
                history = history.strip().split('\n')
                if ctag not in history:
                    print '* ERROR in', package, ': could not find tag', ctag, \
                        'in changelog'
                    continue
                if ntag not in history:
                    print '* ERROR in', package, ': could not find tag', ntag, \
                        'in changelog'
                    continue
                packages_data[package] = history[history.index(ntag):history.index(ctag)]
        
        # change tag headlines to: * package ntag, remove empty lines
        # and indent any other row with 4 spaces
        old_entry_format = re.compile('^([ ]*)\* (\[(.*?)\]){0,1}(.{2,}}?)\[(.*?)\]')
        skip_next = False
        for package, diff in packages_data.items():
            for i, line in enumerate(diff):
                line = aggressive_decode(line).encode('utf8')
                next_line = len(diff)>(i+1) and diff[i+1] or None
                if skip_next:
                    skip_next = False
                    continue
                elif len(line.strip())==0:
                    continue
                elif next_line and (next_line==len(line)*'-' or next_line==len(line)*'='):
                    # current line is a tag-name, next line contains only '-' or '='
                    print ''
                    print '*', package, '-', line.strip()
                    skip_next = True
                else:
                    # check the format
                    old_entry = old_entry_format.search(line)
                    if old_entry:
                        indent, foo, date, text, author = old_entry.groups()
                        print '  ', indent, '*', text.strip()
                        date_author = date and '%s, %s' % (date, author) or author
                        print '    ', indent, '[%s]' % date_author
                    else:
                        print '   ', line

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
                if path in loaded:
                    return
                loaded.append(path)
                if file.startswith('http'):
                    path = self.download_file(file)
                parser.read(path)
                if parser.has_option('buildout', 'extends'):
                    extend_files = parser.get('buildout', 'extends').split()
                    parser.remove_option('buildout', 'extends')
                    for file in extend_files:
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
        dependencies = [(scm.get_package_name('.'), None)]
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
        dependencies = list(set(dependencies))
        dependencies.sort()
        return dependencies

    def download_file(self, url):
        """ Download file from *url*, store it in a tempfile and return its path
        """
        if not getattr(self, '_temporary_downloaded', None):
            # we need to keep a reference to the tempfile, otherwise it will be deleted
            # imidiately
            self._temporary_downloaded = []
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        data = response.read()
        file_ = tempfile.NamedTemporaryFile()
        self._temporary_downloaded.append(file_)
        file_.write(data)
        file_.flush()
        return file_.name

    def delete_downloaded_files(self):
        for file_ in getattr(self, '_temporary_downloaded', []):
            try:
                file_.close()
            except:
                pass
            if os.path.exists(file_.name):
                os.remove(file_)

basecommand.registerCommand(DependencyCheckCommand)
