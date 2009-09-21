"""
SCM Wrapper
"""

import os

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
def get_package_root_path(directory_or_url):
    url_here = get_svn_url(directory_or_url)
    svn.check_project_layout(url_here)
    url_root = get_package_root_url(directory_or_url)
    url_rel = url_here[len(url_root)+1:].split('/')
    if url_rel[0] in ('trunk', 'tags'):
        url_rel.pop(0)
    elif url_rel[0] in ('branches',):
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

