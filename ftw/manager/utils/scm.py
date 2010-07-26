"""
SCM Wrapper
"""

from ftw.manager.utils import input
from ftw.manager.utils import output
from ftw.manager.utils import runcmd_with_exitcode, runcmd, runcmd_unmemoized
from ftw.manager.utils.memoize import memoize
from ftw.manager.utils.singleton import Singleton
from xml.dom import minidom
import distutils.core
import git
import os
import re
import shutil
import simplejson
import subversion as svn
import tempfile

is_git = git.is_git
is_subversion = svn.is_subversion
is_git_svn = git.is_git_svn
IGNORE_EGGS = [
    'setuptools',
    'Plone',
    ]

_marker = object()


class NotAScm(Exception):
    pass

def require_package_root_cwd():
    """ Finds the next package-root relative to the current directory (cwd)
    and tries to switch the python cwd to that path.
    """
    original_cwd = os.getcwd()
    setattr(os, '_original_cwd', original_cwd)
    cwd = original_cwd
    # we need a proper context (providing a svn url). is_package_root will check
    if not is_package_root(cwd):
        current_url = get_svn_url(cwd).split('/')
        root_url = get_package_root_url(cwd).split('/')
        levels = len(current_url) - len(root_url)
        if 'trunk' in current_url:
            levels -= 1
        if 'tags' in current_url or 'branches' in current_url:
            levels -= 2
        if levels>0:
            # change cwd to root
            new_cwd = '/'.join(cwd.split('/')[:-levels])
            os.chdir(new_cwd)

@memoize
def get_svn_url(directory_or_url):
    if is_subversion(directory_or_url):
        return svn.get_svn_url(directory_or_url)
    elif is_git(directory_or_url):
        return git.get_svn_url(directory_or_url)
    raise NotAScm

@memoize
def get_package_root_url(directory_or_url):
    if is_git(directory_or_url):
        return git.get_package_root_url(directory_or_url)
    elif is_subversion(directory_or_url):
        return svn.get_package_root_url(directory_or_url)
    raise NotAScm

@memoize
def get_package_root_path(directory_or_url):
    url_here = get_svn_url(directory_or_url)
    svn.check_project_layout(url_here)
    url_root = get_package_root_url(directory_or_url)
    url_rel = url_here[len(url_root)+1:].split('/')
    if url_rel[0] in ('trunk'):
        url_rel.pop(0)
    elif url_rel[0] in ('branches', 'tags'):
        url_rel.pop(0)
        url_rel.pop(0)
    else:
        raise Exception('Confused: check your svn project layout')
    return os.path.abspath('../' * len(url_rel))

@memoize
def get_package_name(directory_or_url):
    if is_git(directory_or_url):
        return git.get_package_name(directory_or_url)
    elif is_subversion(directory_or_url):
        return svn.get_package_name(directory_or_url)
    raise NotAScm

@memoize
def has_local_changes(path):
    if is_git(path):
        return git.has_local_changes(path)
    elif is_subversion(path):
        return svn.has_local_changes(path)
    raise NotAScm

@memoize
def is_scm(path):
    return is_subversion(path) or is_git(path)

@memoize
def lazy_is_scm(path):
    if os.path.isdir(os.path.join(path, '.git')):
        return True
    elif os.path.isdir(os.path.join(path, '.svn')):
        return True
    else:
        return False

@memoize
def is_package_root(directory_or_url):
    svn_url = get_svn_url(directory_or_url)
    svn_url = svn_url.strip()
    if svn_url.endswith('/'):
        svn_url = svn_url[:-1]
    parts = svn_url.split('/')
    last = parts[-1]
    second_last = parts[-2]
    return last=='trunk' or second_last in ('tags', 'branches')

@memoize
def get_egginfo_for(package, trunk=True, branch=False,
                    tag=False, name='', extra_require=None):
    """ Checks out a package and returns its setup module
    """
    if (trunk and branch and tag) or (not trunk and not branch and not tag):
        raise ValueError('Excepts one and only one of trunk, branch ' +\
                             'and tag to be positive')
    if branch or tag and not name:
        raise ValueError('Provide a branch/tag name')
    dir = tempfile.mkdtemp(suffix='-' + package)
    prev_cwd = os.getcwd()
    os.chdir(dir)
    egg = None
    try:
        pkg_url = PackageSourceMemory().guess_url(package)
        if trunk:
            co_url = os.path.join(pkg_url, 'trunk')
        elif branch:
            co_url = os.path.join(pkg_url, 'branches', name)
        elif tag:
            co_url = os.path.join(pkg_url, 'tags', name)
        cmd = 'svn co %s %s' % (co_url, dir)
        if runcmd_with_exitcode(cmd, log=False)!=0:
            raise Exception('Failed to checkout %s' % package)
        if not os.path.isfile('setup.py'):
            raise Exception('Could not find setup.py in checkout of %s' % package)
        egg = distutils.core.run_setup('setup.py')
    except:
        os.chdir(prev_cwd)
        shutil.rmtree(dir)
        raise
    else:
        os.chdir(prev_cwd)
        shutil.rmtree(dir)
    return egg

def get_egg_dependencies(egg, with_extra=None):
    """ Returns a splitted list of egg dependencies of the distutils egg object
    [
    ('my.egg', None, None),
    ('another.egg', 'a_extra', '1.2'),
    ]
    """
    def _prepare_dependencies(entries):
        for entry in entries:
            name = entry.split('=')[0].split('<')[0].split('>')[0].strip()
            extra = None
            if '[' in name:
                extra = name.split('[')[1].split(']')[0]
                name = name.split('[')[0]
            version = None
            if '=' in entry:
                version = entry.split('=')[-1].strip()
            if name not in IGNORE_EGGS:
                yield (name, extra, version)
    # ---

    entries = list(egg.install_requires)
    dependencies = list(_prepare_dependencies(entries))
    if with_extra and egg.extras_require:
        for extra, entries in egg.extras_require.items():
            if extra == with_extra or with_extra == '*':
                dependencies.extend(list(_prepare_dependencies(entries)))
    return dependencies


def add_and_commit_files(message, files='*'):
    """Adds and commits files to the scm. The repository
    must be .
    Use files='*' to commit all changed files
    """
    commit_all_files = files in ('*', '.')
    if not commit_all_files and type(files) in (unicode, str):
        files = [files]
    if is_subversion('.'):
        if commit_all_files:
            runcmd_unmemoized('svn add *')
        else:
            for file_ in files:
                runcmd_unmemoized('svn add %s' % file_)
    elif is_git('.'):
        if commit_all_files:
            runcmd_unmemoized('git add .')
        else:
            for file_ in files:
                runcmd('git add %s' % file_)
    else:
        raise Exception('unknown scm')
    commit_files(message, files=files)

def commit_files(message, files=''):
    """Commit some files
    """
    commit_all_files = files in ('*', '.')
    if not commit_all_files and type(files) in (unicode, str):
        files = [files]

    if is_subversion('.'):
        if commit_all_files:
            runcmd_unmemoized('svn commit -m "%s"' % (message))
        else:
            runcmd_unmemoized('svn commit -m "%s" %s' % (message,
                                                         ' '.join(files)))

    elif is_git('.'):
        if commit_all_files:
            runcmd_unmemoized('git add .')
        else:
            for file_ in files:
                runcmd('git add %s' % file_)
        runcmd_unmemoized('git commit -m "%s"' % message)
        if is_git_svn('.'):
            runcmd_unmemoized('git svn dcommit')


    else:
        raise Exception('unkown scm')

def remove_files(files):
    """Removes and untrack each file of `files`.
    This just runs commands like "svn remove bla.txt", but it does not commit

    """
    if type(files) in (unicode, str):
        files = (files,)
    if is_subversion('.'):
        runcmd_unmemoized('svn remove %s' % ' '.join(files))
    elif is_git('.'):
        runcmd_unmemoized('git rm %s' % ' '.join(files))


class PackageInfoMemory(Singleton):
    """ Stores following informations about packages:
    * name (key)
    * tags
    * untagged changes
    * svn revision
    * svn url
    """

    def __init__(self):
        if not os.path.isdir(self.cachedir):
            os.mkdir(self.cachedir)

    @property
    @memoize
    def cachedir(self):
        return os.path.abspath(os.path.expanduser('~/.ftw.manager/infocache'))

    @memoize
    def get_info(self, package, force_reload=False, prompt=True):
        svn_url = PackageSourceMemory().guess_url(package, prompt=prompt)
        if not svn_url:
            return None
        data = self.get_cached_info(package)
        update = force_reload
        rev = self.get_revision_for(package)
        if not data:
            update = True
        elif rev>data['rev']:
            update = True
        if update:
            svn.check_project_layout(svn_url)
            data = {
                'name' : package,
                'tags' : svn.get_existing_tags(svn_url),
                'newest_tag' : '',
                'changes' : False,
                'rev' : rev,
                'url' : svn_url,
                'history' : None,
                }
            if data['tags']:
                # find newest tag
                tags = [k for k, v in data['tags'].items()]
                tags.sort(lambda a,b:cmp(data['tags'][a], data['tags'][b]))
                tags.reverse()
                newest_tag = tags[0]
                data['newest_tag'] = newest_tag
                newest_tag_url = os.path.join(svn_url,
                                              'tags',
                                              newest_tag)
                trunk_url = os.path.join(svn_url, 'trunk')
                rows = runcmd_with_exitcode(
                    'svn diff %s %s --summarize' % (trunk_url, newest_tag_url),
                    log=False, respond=True)[1].strip().split('\n')
                for row in rows:
                    flag, url = re.split('\W*', row.strip(), maxsplit=1)
                    url = url.strip()
                    if url.startswith(os.path.join(trunk_url,
                                                   package.replace('.', '/'))) \
                                                   and not url.endswith('version.txt'):
                                                   data['changes'] = True
                                                   break
            else:
                data['changes'] = True
            self.set_cached_info(package, data)
        return data

    @memoize
    def get_history_for(self, package, tag, force_reload=False, prompt=True):
        data = self.get_info(package, force_reload, prompt)
        if not data:
            return None
        history = data.get('history', None)
        if history is not None and history.get(tag, False):
            return history[tag]
        else:
            history = {}
            svn_url = PackageSourceMemory().guess_url(package, prompt=prompt)
            subpath = tag=='trunk' and 'trunk' or 'tags/%s' % tag
            file_url = os.path.join(svn_url, subpath, 'docs', 'HISTORY.txt')
            cmd = 'svn cat %s' % file_url
            history[tag] = runcmd_with_exitcode(cmd, log=False, respond=True)[1]
            data = self.get_cached_info(package)
            data['history'] = history
            self.set_cached_info(package, data)
            return history[tag]

    def get_revision_for(self, package):
        url = PackageSourceMemory().guess_url(package)
        url = '/'.join(url.split('/')[:-1])
        cmd = 'svn ls --xml %s' % url
        xmldata = ''.join(runcmd(cmd, log=False, respond=True))
        doc = minidom.parseString(xmldata)
        for entry in doc.getElementsByTagName('entry'):
            if entry.getElementsByTagName('name')[0].firstChild.nodeValue.strip()==package:
                return entry.getElementsByTagName('commit')[0].getAttribute('revision')
        return None

    def get_cached_info(self, package):
        path = os.path.join(self.cachedir, package)
        if os.path.isfile(path):
            return simplejson.loads(open(path).read())
        return None

    def set_cached_info(self, package, data):
        path = os.path.join(self.cachedir, package)
        file = open(path, 'w')
        file.write(simplejson.dumps(data))
        file.close()

    @memoize
    def get_dependencies_for(self, package, trunk=True, branch=False,
                             tag=False, name='', force_reload=False,
                             prompt=False, with_extra=None):
        """ Returns a list of dependencies (may contain version pinnings) of
        a package in trunk, branch or tag
        """
        # validate parameters
        if (trunk and branch and tag) or (not trunk and not branch and not tag):
            raise ValueError('Excepts one and only one of trunk, branch ' +\
                                 'and tag to be positive')
        if branch or tag and not name:
            raise ValueError('Provide a branch/tag name')

        # get package info
        data = self.get_info(package, force_reload, prompt)
        if not data:
            # we expect that get_info already has set some infos, so this case
            # should usually not happen, but its not an error.
            return None

        subdir = self._calculate_svn_subpath(trunk=trunk, branch=branch, tag=tag,
                                             name=name, with_extra=with_extra)

        # use cached dependency infos from package info, if existing
        if not force_reload and data.get('dependencies', None):
            if data['dependencies'].get(subdir, _marker) != _marker:
                return data['dependencies'][subdir]

        # .. if not existing, get egginfo and update
        try:
            egg = get_egginfo_for(package, trunk=trunk, branch=branch,
                                  tag=tag, name=name, extra_require=with_extra)
        except Exception, exc:
            output.error('Error while loading setup.py of %s (%s): %s' % (
                    package,
                    subdir,
                    str(exc)))
            return []
        dependencies = get_egg_dependencies(egg, with_extra)
        if not data.get('dependencies', None):
            data['dependencies'] = {}
        data['dependencies'][subdir] = dependencies
        self.set_cached_info(package, data)
        return dependencies

    @memoize
    def get_maintainer_for(self, package, trunk=True, branch=False,
                           tag=False, name='', force_reload=False,
                           prompt=False, with_extra=None):
        """ Returns the maintainer of a package in trunk / branch / tag.
        The maintainer is cached in the package infos. The with_extra may
        be used for caching purpose.
        """
        # validate parameters
        if (trunk and branch and tag) or (not trunk and not branch and not tag):
            raise ValueError('Excepts one and only one of trunk, branch ' +\
                                 'and tag to be positive')
        if branch or tag and not name:
            raise ValueError('Provide a branch/tag name')

        # get package info
        data = self.get_info(package, force_reload, prompt)
        if not data:
            # we expect that get_info already has set some infos, so this case
            # should usually not happen, but its not an error.
            return None

        subdir = self._calculate_svn_subpath(trunk=trunk, branch=branch, tag=tag,
                                             name=name, with_extra=with_extra)

        # use cached maintainer infos from package info, if existing
        if not force_reload and data.get('maintainer', None):
            if data['maintainer'].get(subdir, _marker) != _marker:
                return data['maintainer'][subdir]

        # .. if not existing, get egginfo and update
        try:
            egg = get_egginfo_for(package, trunk=trunk, branch=branch,
                                  tag=tag, name=name, extra_require=with_extra)
        except Exception, exc:
            output.error('Error while loading setup.py of %s (%s): %s' % (
                    package,
                    subdir,
                    str(exc)))
            return []

        maintainer = egg.get_maintainer()

        # the maintainer may be changed in a branch or tag, so we store it for
        # every "version" of a package (trunk, branches, tags). Use the subdir
        # as key in the caching dictionary
        if not data.get('maintainer', None):
            data['maintainer'] = {}
        data['maintainer'][subdir] = maintainer
        self.set_cached_info(package, data)
        return maintainer

    def _calculate_svn_subpath(self, trunk=True, branch=False,
                               tag=False, name='', with_extra=None):
        """calculate svn path relative to package root, since infos may
        change in different branches

        """
        subdir = None
        if trunk:
            subdir = 'trunk'
        elif branch:
            subdir = os.path.join('branches', name)
        elif tag:
            subdir = os.path.join('tags', name)
        if with_extra:
            subdir += '[%s]' % with_extra
        return subdir


class PackageSourceMemory(Singleton):

    def __init__(self):
        self._packages = {}
        for row in open(self.cache_path).read().split('\n'):
            row = row.strip()
            if row:
                name, url = row.split('=')
                self._packages[name.strip()] = url.strip()

    @property
    @memoize
    def cache_path(self):
        confdir = os.path.expanduser('~/.ftw.manager/')
        if not os.path.isdir(confdir):
            os.mkdir(confdir)
        cachefile = os.path.join(confdir, 'packages')
        if not os.path.isfile(cachefile):
            open(cachefile, 'w').close()
        return cachefile

    def has_package(self, name):
        return name in self._packages

    def set(self, name, url):
        name = name.strip()
        url = url.strip()
        file = open(self.cache_path, 'a+')
        file.write(' = '.join((name, url)))
        file.write('\n')
        file.close()
        self._packages[name] = url

    def get(self, name, *args, **kwargs):
        return self._packages.get(name, *args, **kwargs)

    @memoize
    def guess_url(self, package, prompt=False, required=False):
        """ Tries to guess the url of a package. If it's not able to guess, it asks
        or returns None, dependening on *prompt*
        """
        # first, we check if we already know the name
        if self.has_package(package):
            return self.get(package)
        # we will search some places, make a list of possible hint-directories
        hint_dirs = []
        # the parent directory may contain the package or other packages with the same
        # namespace (e.g. src-directory)
        hint_dirs.append(os.path.abspath('..'))
        # the gitsvn-cache directory contains several packages, the required package or
        # a package with the same namespace?
        hint_dirs.append(os.path.abspath(git.get_gitsvn_cache_path()))

        # now we try to find the package in the hint_dirs
        for dir in hint_dirs:
            path = os.path.join(dir, package)
            if os.path.isdir(path) and is_scm(path):
                url = get_package_root_url(path)
                self.set(package, url)
                return url

        # now lets guess it with the namespace...
        # first we check the packages we alreay know the path:
        namespace = package.split('.')[0]
        for pkg, url in self._packages.items():
            if pkg.startswith('%s.' % namespace):
                try:
                    dir_url = '/'.join(url.split('/')[:-1])
                    if package+'/' in svn.listdir(dir_url):
                        url = os.path.join(dir_url, package)
                        self.set(package, url)
                        return url
                except NotAScm:
                    pass

        # ok, now we need to check our hint_dirs for packages with the same namespace
        for dir in hint_dirs:
            for pkg in os.listdir(dir):
                path = os.path.join(dir, pkg)
                if pkg.startswith('%s.' % namespace):
                    try:
                        pkg_url = self.guess_url(pkg, prompt=False)
                        dir_url = '/'.join(pkg_url.split('/')[:-1])
                        if package+'/' in svn.listdir(dir_url):
                            url = os.path.join(dir_url, package)
                            self.set(package, url)
                            return url
                    except NotAScm:
                        pass

        # could not find any? we may need to ask the user...
        if prompt:
            def input_validator(v):
                if not required and not v:
                    return True
                if not v or not svn.isdir(v.strip()):
                    return 'Invalid SVN-URL'
                return True
            colorized_package = output.colorize(package, output.BOLD_WARNING)
            msg = output.colorize('I\'m having trouble to guess the SVN-URL for the package',
                                  output.WARNING)
            msg += ' ' + colorized_package
            print msg
            msg = 'SVN-URL of %s'  % colorized_package
            if not required:
                msg += output.colorize(' or nothing', output.WARNING)
            url_input = input.prompt(msg, input_validator)
            if url_input:
                url = svn.get_package_root_url(url_input)
                self.set(package, url)
                return url
        return None


@memoize
def guess_package_url(*args, **kwargs):
    return PackageSourceMemory().guess_url(*args, **kwargs)
