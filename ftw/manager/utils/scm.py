"""
SCM Wrapper
"""

import os

import git
import subversion as svn
from ftw.manager.utils.memoize import memoize
from ftw.manager.utils.singleton import Singleton
from ftw.manager.utils import input
from ftw.manager.utils import output

is_git = git.is_git
is_subversion = svn.is_subversion

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
    if is_git(directory_or_url):
        return git.get_svn_url(directory_or_url)
    elif is_subversion(directory_or_url):
        return svn.get_svn_url(directory_or_url)
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
def is_package_root(directory_or_url):
    svn_url = get_svn_url(directory_or_url)
    svn_url = svn_url.strip()
    if svn_url.endswith('/'):
        svn_url = svn_url[:-1]
    parts = svn_url.split('/')
    last = parts[-1]
    second_last = parts[-2]
    return last=='trunk' or second_last in ('tags', 'branches')



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
