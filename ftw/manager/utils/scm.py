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

