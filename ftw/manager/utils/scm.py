"""
SCM Wrapper
"""

import git
import subversion as svn
from ftw.manager.utils.memoize import memoize

is_git = git.is_git
is_subversion = svn.is_subversion

class NotAScm(Exception):
    pass


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
def get_package_name(directory_or_url):
    if is_git(directory_or_url):
        return git.get_package_name(directory_or_url)
    elif is_subversion(directory_or_url):
        return svn.get_package_name(directory_or_url)
    raise NotAScm

