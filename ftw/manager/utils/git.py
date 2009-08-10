"""
contains git-svn helper methods
"""

from ftw.manager.utils import runcmd
from ftw.manager.utils.memoize import memoize

class NotAGitsvnRepository(Exception):
    pass

@memoize
def is_git(directory):
    """
    Checks if a directory is a local git repo
    """
    return 'Repository Root' in ''.join(runcmd('git svn info', log=False, respond=True))

@memoize
def get_package_name(directory_or_url):
    return get_package_root_url(directory_or_url).split('/')[-1]

@memoize
def get_package_root_url(directory_or_url):
    """
    Guesses the root svn-url of a package checked out in directory.
    The package must have a svn default layout (with trunk, branches and tags)
    """
    url = get_svn_url(directory_or_url)
    urlparts = url.split('/')
    if not sum([int(x in urlparts) for x in ('trunk', 'branches', 'tags')])>0:
        raise InvalidProjectLayout
    for dir in ('trunk', 'branches', 'tags'):
        if dir in urlparts:
            return '/'.join(urlparts[:urlparts.index(dir)])

@memoize
def get_svn_url(directory_or_url):
    if sum([int(directory_or_url.startswith(x)) for x in ('https://', 'http://', 'svn:')])>0:
        return directory_or_url
    else:
        directory = directory_or_url
        if not is_git(directory):
            raise NotAGitsvnRepository
        return ''.join(runcmd('git svn info %s | grep URL | cut -d " " -f 2' % directory, log=False, respond=True)).strip()
