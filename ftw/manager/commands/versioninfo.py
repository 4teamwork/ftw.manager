from ftw.manager.commands import basecommand
from ftw.manager.utils import output
from ftw.manager.utils import scm
from ftw.manager.utils.http import HTTPRealmFinder
from ftw.manager.utils.memoize import memoize
from ftw.manager.utils.output import error
from pkg_resources import parse_version, Requirement
from setuptools import package_index
import ConfigParser
import distutils.core
import os
import tempfile
import urllib2


class VersioninfoCommand(basecommand.BaseCommand):
    u"""
    This command searches all version pinnings for a specific package in
    the buildout configuration. It walks up the `extends`-list and follows
    remote KGS systems.

    The buildout config file to use can be specificed the option `-c <FILE.cfg>`,
    if the option is not used it defaults to buildout.cfg in the current working
    directory.

    The option `-n` tries to find new releases of this egg.

    Its possible to use this command for multiple packages by calling the command
    with each package as a parameter, but its also possible to use the command on
    a list of dependencies which are defined in ./setup.py

    """

    command_name = u'versioninfo'
    command_shortcut = u'vi'
    description = u'Prints version pinning information'
    usage = u'ftw %s [-n] [-c <buildout.cfg>] [-d] '  % command_name + \
        u'[<package1> [<package2> [...]]]'

    def __call__(self):
        output.warning('This command does not support git packages')
        pinnings = self._get_pinnings_by_package()
        def _format_line(pkg, extra, version, file, current=False):
            pkgname = pkg
            if extra:
                pkgname += '[%s]' % extra
            if current:
                indent = ' ' * 4 + '*'
            else:
                indent = ' ' * 5
            txt = ' '.join((indent, pkgname, '=', version, '@', file))
            if current:
                return output.colorize(txt, output.WARNING)
            else:
                return txt
        first = True
        for pkg, dep_extra, dep_version in self._get_packages():
            current_version = None
            if first:
                first = False
            else:
                print ''
                print ''
            print output.colorize(pkg, output.INFO)
            if dep_version:
                current_version = None
                print _format_line(pkg, dep_extra, dep_version, './setup.py')
            if pkg.lower() in pinnings.keys():
                pkg_pinnings = pinnings[pkg.lower()][:]
                pkg_pinnings.reverse()
                for file, extra, version in pkg_pinnings:
                    if not current_version:
                        current_version = version
                        print _format_line(pkg, extra, version, file, current=True)
                    else:
                        print _format_line(pkg, extra, version, file)
            if self.options.new:
                new_dists = self._get_newer_versions_for(pkg, current_version)
                if len(new_dists) > 0:
                    print output.colorize('newer distributions than %s:' % current_version,
                                          output.ERROR)
                    for dist in new_dists:
                        print ' ' * 5, output.colorize(dist, output.ERROR)

    def register_options(self):
        self.parser.add_option('-n', '--new', dest='new',
                               action='store_true', default=False,
                               help='Searches for newer versions')
        self.parser.add_option('-d', '--dependencies', dest='dependencies',
                               action='store_true', default=False,
                               help='Run with dependency packages in ./setup.py')
        self.parser.add_option('-c', '--config', dest='buildout',
                               action='store', default='./buildout.cfg',
                               help='Buildout config file containing version infos')

    def _get_newer_versions_for(self, pkg, version):
        if version == None:
            version = ''
        # There is a problem when using find-links for eggs which are on the pypi
        # so we need to use two different indexes
        # - self.pi : index using find-links
        try:
            self.pi
        except AttributeError:
            self.pi = package_index.PackageIndex()
            self.pi.add_find_links(self.find_links)
        # - self.pypi : index only for pypi
        try:
            self.pypi
        except AttributeError:
            self.pypi = package_index.PackageIndex()

        # first we try it using find-links
        index = self.pi
        req = Requirement.parse(pkg)
        index.package_pages[req.key] = self.find_links
        try:
            index.find_packages(req)
        except TypeError:
            # .. that didnt work, so lets try it without find-links.. we need to
            # use the "fresh" self.pypi index
            index = self.pypi
            index.find_packages(req)
        parsed_version = parse_version(version)
        new_dists = []
        for dist in index[req.key]:
            if dist.parsed_version > parsed_version:
                new_dists.append('%s = %s' % (dist.project_name, dist.version))
        return tuple(set(new_dists))


    @memoize
    def _get_packages(self):
        """ Returns a list of [(pkgname, extra, version),(...)]
        including parameter packages and dependency packages
        """
        packages = list([(pkg, None, None) for pkg in self.args])
        if self.options.dependencies:
            packages.extend(self._get_dependency_packages())
        if len(packages)==0:
            try:
                packages.append((scm.get_package_name('.'), None, None))
            except:
                # maybe we are not in a package - thats not a error
                pass
        if len(packages)==0:
            # maybe we are in a src folder.. use every item
            for pkg in os.listdir('.'):
                packages.append((pkg, None, None))
        return packages

    @memoize
    def _get_dependency_packages(self):
        dependencies = [(scm.get_package_name('.'), None, None)]
        dependencies += scm.get_egg_dependencies(self.egg)
        return dependencies

    @property
    @memoize
    def egg(self):
        if os.path.isfile('setup.py'):
            return distutils.core.run_setup('setup.py')
        else:
            return None


    @memoize
    def _get_pinnings_by_package(self):
        """ Example:
        {
        'foo.bar': [('buildout.cfg', 'a_extra', '1.5'), (...)],
        }
        """
        data_by_file = self._get_buildout_pinning_mapping()
        data = {}
        for file, packages in data_by_file:
            for pkg, extra, version in packages:
                if pkg.lower() not in data.keys():
                    data[pkg.lower()] = []
                data[pkg.lower()].append((file, extra, version))
        return data

    @memoize
    def _get_buildout_pinning_mapping(self):
        """ Example:
        (
        ('buildout.cfg', (('foo.bar', None, '1.7'), (...))),
        ('http://kgs...', (('foo.bar', 'a_extra', '1.3'))),
        )
        """
        buildout_file = os.path.abspath(self.options.buildout)
        self.find_links = []
        if not os.path.isfile(buildout_file):
            error('Buildout not found at %s' % buildout_file,
                  exit=True)
        # load buildout with config parsers
        data = []
        loaded = []
        version_section_name = 'versions'

        # load extends
        def load_extends(file, dir):
            if file.startswith('http'):
                # kgs / http
                path = self._download_file(file)
            else:
                # local
                path = os.path.join(dir, file)

            # is it already loaded?
            if path in loaded:
                return

            # load it
            parser = ConfigParser.SafeConfigParser()
            parser.read(path)
            loaded.append(path)

            # get the defined versions
            if parser.has_section(version_section_name):
                subdata = []
                for pkg, version in parser.items(version_section_name):
                    extra = None
                    if '[' in pkg and ']' in pkg:
                        extra = pkg.split('[')[1].split(']')[0]
                    subdata.append((pkg, extra, version))
                # make a pretty relative name
                pretty_name = file
                if path.startswith(os.path.dirname(buildout_file)):
                    pretty_name = path[len(os.path.dirname(buildout_file))+1:]
                data.insert(0, (pretty_name, subdata))

            # follow extends
            if parser.has_option('buildout', 'extends'):
                extend_files = parser.get('buildout', 'extends').split()
                for file in extend_files:
                    load_extends(file.strip(), os.path.dirname(path))

            # remember find_links
            if parser.has_option('buildout', 'find-links'):
                for link in parser.get('buildout', 'find-links').split():
                    link = link.strip()
                    if link:
                        self.find_links.append(link)

        load_extends(os.path.basename(buildout_file),
                     os.path.abspath(os.path.dirname(buildout_file)))

        return data


    def _download_file(self, url):
        """ Download file from *url*, store it in a tempfile and return its path
        """
        if not getattr(self, '_temporary_downloaded', None):
            # we need to keep a reference to the tempfile, otherwise it will be deleted
            # imidiately
            self._temporary_downloaded = []

        if '@' in url:
            # http basic auth in url

            # remove credentials part from url
            protocol, rest = url.split('://', 1)
            protocol += '://'
            credentials, rest = rest.split('@', 1)
            url = protocol + rest

            realm = HTTPRealmFinder(url).get()

            # install a basic auth handler
            if ':' in credentials:
                user, password = credentials.split(':', 1)
            else:
                user, password = credentials, None

            auth_handler = urllib2.HTTPBasicAuthHandler()
            auth_handler.add_password(realm=realm,
                                      uri=url,
                                      user=user,
                                      passwd=password)
            opener = urllib2.build_opener(auth_handler)
            urllib2.install_opener(opener)

        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        data = response.read()
        file_ = tempfile.NamedTemporaryFile()
        self._temporary_downloaded.append(file_)
        file_.write(data)
        file_.flush()
        return file_.name

basecommand.registerCommand(VersioninfoCommand)
