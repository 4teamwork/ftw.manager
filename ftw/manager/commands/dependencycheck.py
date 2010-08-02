from ftw.manager.commands import basecommand
from ftw.manager.utils import aggressive_decode
from ftw.manager.utils import output
from ftw.manager.utils import scm
from ftw.manager.utils.memoize import memoize
import ConfigParser
import distutils.core
import os
import re
import tempfile
import urllib2


class DependencyCheckCommand(basecommand.BaseCommand):
    u"""
    The "dependencycheck" Command checks the dependencies of your package and
    displays a table of all packages you have a dependency to.
    The command checks for each package if there is a new SVN tag.

    Run the command on the root of your package checkout, where your setup.py
    is.

    Caching
    The results are cached in `~/.ftw.manager` for faster access. If you do
    not trust the caching algorithm you can force a refresh with `--refresh`.

    Generated History
    WIth the `--history` option it is possible to generate a history using
    the `HISTORY.txt` files of each package which has changes in trunk or
    tag (dependending on `--dev` option).

    """

    command_name = u'dependencycheck'
    command_shortcut = u'dc'
    description = u'Check Dependencies'
    usage = u'ftw %s [OPTIONS]' % command_name

    def register_options(self):
        self.parser.add_option('-r', '--refresh', dest='refresh',
                               action='store_true', default=False,
                               help='Force refresh. Recalculates all infos')
        self.parser.add_option('-c', '--config', dest='buildout',
                               action='store', default=None,
                               help='Buildout config file containing version '
                               'infos')
        self.parser.add_option('-v', '--verbose', dest='verbose',
                               action='store_true', default=False,
                               help='Print executed commands')
        self.parser.add_option('-H', '--history', dest='history',
                               action='store_true', default=False,
                               help='Generate history file with all packages '
                               'with a new version')
        self.parser.add_option('-d', '--dev', dest='history_dev',
                               action='store_true', default=False,
                               help='List packages with modified trunk when '
                               'using --history option')
        self.parser.add_option('-l', '--limit', dest='limit',
                               action='store', default=0,
                               help='Set depth limit (default 0)')
        self.parser.add_option('-q', '--quiet', dest='quiet',
                               help='Do not ask anything',
                               action='store_true', default=False)
        self.parser.add_option('-p', '--pinning-proposal',
                               dest='pinning_proposal',
                               help='Show a list of packages to upgrade with '
                               'their newest version in version pinning '
                               'format.',
                               action='store_true', default=False)

    def __call__(self):
        if not self.options.quiet:
            output.warning('Git repositories are not supported yet!')
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
            'Maintainer',
            )
        table = output.ASCIITable(*titles)
        versions = self.package_versions
        force_reload = self.options.refresh
        limit = int(self.options.limit)
        pinnings = {}
        if limit < 0:
            limit += 1

        def _add_rows(dependencies, indent=0):
            for package, extra, v in dependencies:
                color = None
                ctag = package in versions.keys() and \
                    str(versions[package]) or ''
                info = scm.PackageInfoMemory().get_info(
                    package,
                    force_reload=force_reload,
                    prompt=(not self.options.quiet))
                maintainer = scm.PackageInfoMemory().get_maintainer_for(
                    package, with_extra=extra) or ''
                ntag = info and str(info['newest_tag']) or ''
                if ntag and ctag:
                    if ntag < ctag:
                        ntag = output.colorize(ntag, output.WARNING)
                        color = output.WARNING
                    elif ntag > ctag:
                        ntag = output.colorize(ntag, output.ERROR)
                        color = output.ERROR
                        pinnings[package] = ntag
                    elif ntag == ctag:
                        ntag = output.colorize(ntag, output.INFO)
                        color = output.INFO
                elif ntag:
                    pinnings[package] = ntag
                chg = ''
                if info and info['changes']:
                    chg = output.colorize('YES', output.WARNING)
                    color = output.WARNING
                name = extra and '%s[%s]' % (package, extra) or package
                name = '  ' * indent + name
                table.push((
                        color and output.colorize(name, color) or name,
                        ctag,
                        ntag,
                        chg,
                        maintainer,
                        ))
                if indent < limit:
                    sub_deps = scm.PackageInfoMemory().get_dependencies_for(
                        package, with_extra=extra)
                    if sub_deps:
                        _add_rows(sub_deps, indent + 1)
        _add_rows(self.dependency_packages)
        table()
        # ---- show pinning proposal
        if self.options.pinning_proposal:
            print ''
            print '=' * 50
            print 'PINNING PROPOSAL'
            print ''
            for pkg, vers in pinnings.items():
                print pkg, '=', vers

    def print_history(self):
        versions = self.package_versions
        force_reload = self.options.refresh
        packages_data = {}
        list_trunk_modifications = self.options.history_dev
        limit = int(self.options.limit)
        if limit > 0:
            packages = []
            # packages is only *this* package, so lets walk up the dependencies

            def _follow_dependencies(pkg, level=0, extra=None, version=None):
                # add it to the package list
                if pkg not in packages:
                    packages.append([pkg, extra, version])
                if level != limit:
                    # load some infos about the package and cache them
                    scm.PackageInfoMemory().get_info(pkg, prompt=False)
                    # load and follow the dependencies
                    deps = scm.PackageInfoMemory().get_dependencies_for(
                        pkg, with_extra=extra)
                    if deps:
                        for subpkg, subextra, subversion in deps:
                            _follow_dependencies(subpkg, level=level + 1,
                                                 extra=subextra,
                                                 version=subversion)
            _follow_dependencies(scm.get_package_name('.'))
            packages.sort()
        else:
            packages = self.dependency_packages

        for package, extra, v in packages:
            if self.options.verbose:
                print package
            ctag = package in versions.keys() and str(versions[package]) or ''
            info = scm.PackageInfoMemory().get_info(package,
                                                    force_reload=force_reload,
                                                    prompt=False)
            ntag = info and str(info['newest_tag']) or ''
            if list_trunk_modifications and info and info['changes']:
                history = scm.PackageInfoMemory().get_history_for(package,
                                                                  'trunk',
                                                                  prompt=False)
                if not history:
                    continue
                history = history.strip().split('\n')
                if ctag not in history:
                    print '* ERROR in', package, ': could not find tag', ctag,
                    print 'in changelog'
                    continue
                packages_data[package] = history[2:history.index(ctag)]
            elif ntag and ctag and ntag != ctag:
                history = scm.PackageInfoMemory().get_history_for(package,
                                                                  ntag,
                                                                  prompt=False)
                if not history:
                    continue
                history = history.strip().split('\n')
                if ctag not in history:
                    print '* ERROR in', package, ': could not find tag', ctag,
                    print 'in changelog'
                    continue
                if ntag not in history:
                    print '* ERROR in', package, ': could not find tag', ntag,
                    print 'in changelog'
                    continue
                packages_data[package] = history[history.index(ntag):
                                                     history.index(ctag)]

        # change tag headlines to: * package ntag, remove empty lines
        # and indent any other row with 4 spaces
        pat = '^([ ]*)\* (\[(.*?)\]){0,1}(.{2,}}?)\[(.*?)\]'
        old_entry_format = re.compile(pat)
        skip_next = False
        for package, diff in packages_data.items():
            for i, line in enumerate(diff):
                line = aggressive_decode(line).encode('utf8')
                next_line = len(diff) > (i + 1) and diff[i + 1] or None
                if skip_next:
                    skip_next = False
                    continue
                elif len(line.strip()) == 0:
                    continue
                elif next_line and (next_line == len(line) * '-' or
                                    next_line == len(line) * '='):
                    # current line is a tag-name, next line contains
                    # only '-' or '='
                    print ''
                    print '*', package, '-', line.strip()
                    skip_next = True
                else:
                    # check the format
                    old_entry = old_entry_format.search(line)
                    if old_entry:
                        indent, foo, date, text, author = old_entry.groups()
                        print '  ', indent, '*', text.strip()
                        date_author = date and '%s, %s' % (date, author) or \
                            author
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
        for pkg, extra, version in self.dependency_packages:
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
                         os.path.abspath(os.path.dirname(
                        self.options.buildout)))
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
        dependencies = [(scm.get_package_name('.'), None, None)]
        if int(self.options.limit) > 0:
            return dependencies
        if self.egg:
            dependencies += scm.get_egg_dependencies(self.egg, with_extra='*')
        else:
            # source directory ?
            for pkg in os.listdir('.'):
                path = os.path.abspath(pkg)
                if os.path.isdir(path) and scm.lazy_is_scm(path):
                    dependencies.append((pkg, None, None))
        dependencies = list(set(dependencies))
        dependencies.sort()
        return dependencies

    def download_file(self, url):
        """ Download file from *url*, store it in a tempfile and
        return its path

        """
        if not getattr(self, '_temporary_downloaded', None):
            # we need to keep a reference to the tempfile, otherwise it will
            # be deleted imidiately
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
