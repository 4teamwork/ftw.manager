import tempfile
from pkg_resources import parse_version, Requirement
import urllib2
import ConfigParser
import distutils.core
from setuptools import package_index
from ftw.manager.commands import basecommand
from ftw.manager.utils import scm
from ftw.manager.utils.output import error
from ftw.manager.utils.memoize import memoize
import os


class VersioninfoCommand(basecommand.BaseCommand):
    """
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

    command_name = 'versioninfo'
    command_shortcut = 'vi'
    description = 'Prints version pinning information'
    usage = 'ftw %s [-n] [-c <buildout.cfg>] [-d] '  % command_name + \
        '[<package1> [<package2> [...]]]'

    def __call__(self):
        pinnings = self._get_pinnings_by_package()
        def _format_line(pkg, extra, version, file):
            pkgname = pkg
            if extra:
                pkgname += '[%s]' % extra
            return ' '.join((' ' * 5, pkgname, '=', version, '@', file))
        first = True
        current_version = None
        for pkg, dep_extra, dep_version in self._get_packages():
            if first:
                first = False
            else:
                print ''
                print '-' * 50
                print ''
            print pkg
            if dep_version:
                current_version = None
                print _format_line(pkg, dep_extra, dep_version, './setup.py')
            if pkg in pinnings.keys():
                for file, extra, version in pinnings[pkg]:
                    if not current_version:
                        current_version = version
                    print _format_line(pkg, extra, version, file)
            if self.options.new:
                print 'newer distributions than %s:' % current_version
                new_dists = self._get_newer_versions_for(pkg, current_version)
                for dist in new_dists:
                    print ' ' * 5, dist

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
        try:
            self.pi
        except AttributeError:
            self.pi = package_index.PackageIndex()
            self.pi.add_find_links(self.find_links)
        req = Requirement.parse(pkg)
        self.pi.find_packages(req)
        parsed_version = parse_version(version)
        new_dists = []
        for dist in self.pi[req.key]:
            if dist.parsed_version > parsed_version:
                new_dists.append('%s %s' % (dist.project_name, dist.version))
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
                if pkg not in data.keys():
                    data[pkg] = []
                data[pkg].append((file, extra, version))
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
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        data = response.read()
        file_ = tempfile.NamedTemporaryFile()
        self._temporary_downloaded.append(file_)
        file_.write(data)
        file_.flush()
        return file_.name



basecommand.registerCommand(VersioninfoCommand)
