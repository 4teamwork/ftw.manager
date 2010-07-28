"""
contains git-svn helper methods
"""

import os
from ftw.manager.utils import runcmd
from ftw.manager.utils import subversion as svn
from ftw.manager.utils import output
from ftw.manager.utils.memoize import memoize

class NotAGitsvnRepository(Exception):
    pass

@memoize
def is_git(directory):
    """
    Checks if a directory is a local git repo
    """
    directory = os.path.abspath(directory)
    dir = directory.split('/')
    while len(dir) > 1:
        path = '/'.join(dir)
        gitconfig = os.path.join(path, '.git', 'config')
        if os.path.isfile(gitconfig):
            return True
        # if there is .svn (but no .git) it is a .svn directory and
        # do not have to continue walking up...
        if svn.is_subversion(path):
            return False
        dir.pop()
    return False

def is_git_svn(directory):
    directory = os.path.abspath(directory)
    dir = directory.split('/')
    while len(dir)>1:
        path = '/'.join(dir)
        gitconfig = os.path.join(path, '.git', 'config')
        if os.path.isfile(gitconfig) and '[svn-remote' in open(gitconfig).read():
            return True
        # if there is .svn (but no .git) it is a .svn directory and
        # do not have to continue walking up...
        if svn.is_subversion(path):
            return False
        dir.pop()
    return False
    

@memoize
def get_package_name(directory_or_url):
    if not directory_or_url.startswith('http://') and \
            not directory_or_url.startswith('svn://') and \
            is_git(directory_or_url) and not is_git_svn(directory_or_url):
        # directory_or_url is a path and we are in a non-svn git repo, so we have no URL
        # in this case we just take the foldername as package-name, which contains the .git
        dir = os.path.abspath(directory_or_url).split('/')
        while len(dir):
            if os.path.exists(os.path.join('/'.join(dir), '.git')):
                return dir[-1]
            else:
                dir.pop()
    else:
        return get_package_root_url(directory_or_url).split('/')[-1]

@memoize
def get_package_root_url(directory_or_url):
    """
    Guesses the root svn-url of a package checked out in directory.
    The package must have a svn default layout (with trunk, branches and tags)
    """
    url = get_svn_url(directory_or_url)
    urlparts = url.split('/')
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
        return ''.join(runcmd('cd %s; git svn info | grep URL | cut -d " " -f 2' % directory, log=False, respond=True)).strip()

@memoize
def get_gitsvn_cache_path():
    return os.path.expanduser('~/.gitsvn')

def setup_gitsvn_cache():
    """
    Sets up a gitsvn cache at ~/.gitsvn
    """
    path = get_gitsvn_cache_path()
    if not os.path.isdir(path):
        print '* creating local gitsn chache directory at %s' % path
        os.mkdir(path)

def checkout_gitsvn(svn_url, location='.'):
    svn_url = svn_url[-1]=='/' and svn_url[:-1] or svn_url
    root_url = svn.get_package_root_url(svn_url)
    if not svn.isdir(svn_url):
        raise svn.InvalidSubversionURL
    expected_dirs = ('trunk', 'tags', 'branches')
    got_dirs = expected_dirs
    try:
        svn.check_project_layout(svn_url)
    except svn.InvalidProjectLayout:
        # check the directories and print a warning
        dircontent = runcmd('svn ls %s' % svn_url, log=False, respond=True)
        dircontent = [x.strip()[:-1] for x in dircontent]
        got_dirs = []
        missing_dirs = []
        for dir in expected_dirs:
            if dir in dircontent:
                got_dirs.append(dir)
            else:
                missing_dirs.append(dir)
                output.warning('Directory %s missing!' % dir)
    package_name = svn.get_package_name(svn_url)
    cache_path = os.path.join(get_gitsvn_cache_path(), package_name)
    if os.path.exists(package_name):
        raise Exception('%s already existing' % os.path.abspath(package_name))
    gitbranch = svnurl_get_gitbranch(svn_url)
    # clone it
    if os.path.exists(cache_path):
        runcmd('cd %s; git reset --hard' % cache_path)
        runcmd('cd %s; git svn fetch' % cache_path)
        runcmd('cd %s; git svn rebase' % cache_path)
    else:
        if got_dirs==expected_dirs:
            # we have a standard layout
            cmd = 'cd %s; git svn clone --stdlayout %s' % (
                get_gitsvn_cache_path(),
                root_url,
                )
        else:
            # some dirs are missing
            args = ['--%s=%s' % (d,d) for d in got_dirs]
            cmd = 'cd %s; git svn clone %s %s' % (
                get_gitsvn_cache_path(),
                ' '.join(args),
                root_url,
                )
        runcmd(cmd)
    runcmd('cp -r %s %s' % (cache_path, location))
    co_path = os.path.join(location, package_name)
    runcmd('cd %s ; git checkout %s' % (
            co_path,
            gitbranch,
            ))
    runcmd('cd %s ; git reset --hard' % co_path)
    runcmd('cd %s ; git svn rebase' % co_path)


@memoize
def svnurl_get_gitbranch(svn_url):
    root_url = svn.get_package_root_url(svn_url)
    gitbranch = 'master'
    svn_parts = svn_url.split('/')
    if root_url!=svn_url:
        if svn_parts[-2]=='branches':
            gitbranch = 'remotes/%s' % svn_parts[-1]
        elif svn_parts[-2]=='tags':
            gitbranch = 'remotes/tags/%s' % svn_parts[-1]
    return gitbranch

def apply_svn_ignores(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower()=='ignore.txt':
                svnignore = os.path.join(root, file)
                gitignore = os.path.join(root, '.gitignore')
                if not os.path.exists(gitignore):
                    f = open(gitignore, 'w')
                    f.write(open(svnignore).read().strip())
                    f.write('\n')
                    f.write('.gitignore')
                    f.close()

@memoize
def has_local_changes(path):
    cmd = 'cd %s ; git status | grep "\t"' % path
    return len(runcmd(cmd, log=False, respond=True))>0

def pull_changes(path):
    cmd = 'cd %s ; git svn fetch ; git svn rebase' % path
    return runcmd(cmd, log=True, respond=True)

def push_committed_changes(path):
    cmd = 'cd %s ; git svn dcommit' % path
    return runcmd(cmd, log=True, respond=True)
