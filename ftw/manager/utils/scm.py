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

