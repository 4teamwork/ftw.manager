"""
contains subversion helper methods
"""

import os
import xml.dom.minidom
from ftw.manager.utils import runcmd, runcmd_with_exitcode, runcmd_unmemoized
from ftw.manager.utils import output, input
from ftw.manager.utils.memoize import memoize, flush_cache

class NotASubversionCheckout(Exception):
    pass

class InvalidSubversionURL(Exception):
    pass

class InvalidProjectLayout(Exception):
    """
    trunk / branches / tags folder missing
    """
    pass

@memoize
def is_subversion(directory):
    """
    Checks if a directory is a subversion checkout
    """
    return os.path.isdir(os.path.join(directory, '.svn'))

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
    return url

@memoize
def get_svn_url(directory_or_url):
    if sum([int(directory_or_url.startswith(x)) for x in ('https://', 'http://', 'svn:')])>0:
        return directory_or_url
    else:
        directory = directory_or_url
        if not is_subversion(directory):
            raise NotASubversionCheckout
        return ''.join(runcmd('svn info %s | grep URL | cut -d " " -f 2' % directory, log=False, respond=True)).strip()

@memoize
def check_project_layout(directory_or_url, raise_exception=True, ask_for_creation=True):
    """
    Checks if the project has a default svn layout with the folders
    trunk, tags and branches.
    """
    if not raise_exception:
        try:
            url = get_package_root_url(directory_or_url)
        except InvalidProjectLayout:
            return False
    else:
        url = get_package_root_url(directory_or_url)
    dircontent = runcmd('svn ls %s' % url, log=False, respond=True)
    dircontent = [x.strip()[:-1] for x in dircontent]
    # check if there are the expected folders
    excpected = ('trunk', 'tags', 'branches')
    missing = []
    for dir in excpected:
        if dir not in dircontent:
            missing.append(dir)
    # ask what to do, if there are folders missing
    if len(missing)>0:
        if ask_for_creation:
            output.error('[%s] Invalid project layout, folders missing: ' %
                         get_package_name(url) + ', '.join(missing))
            if input.prompt_bool('Would you like to create the missing folders?'):
                cmd = 'svn mkdir '
                cmd += ' '.join([os.path.join(url, dir) for dir in missing])
                cmd += ' -m "created folders: %s for package %s"' % (
                        ', '.join(missing),
                        get_package_name(directory_or_url),
                )
                runcmd(cmd, log=True, respond=True)
                # need to clean caches
                flush_cache(runcmd)
                flush_cache(runcmd_with_exitcode)
                return check_project_layout(directory_or_url, raise_exception=raise_exception, ask_for_creation=False)
        if raise_exception:
            raise InvalidProjectLayout
        else:
            return False
    return True

@memoize
def get_package_name(directory_or_url):
    return get_package_root_url(directory_or_url).split('/')[-1]

@memoize
def get_existing_tags(directory_or_url):
    """
    Returns a dictionary of tags and the revision of the last commit

    {
        u'2.0.4' : u'15433',
        u'2.3' : u'27827',
    }
    """
    tags_dir = os.path.join(get_package_root_url(directory_or_url), 'tags')
    xml_data = ''.join(runcmd('svn ls --xml %s' % tags_dir, log=False, respond=True))
    dom = xml.dom.minidom.parseString(xml_data)
    tags = {}
    for entry in dom.getElementsByTagName('entry'):
        node = entry.getElementsByTagName('name')[0]
        name = ''.join([child.toxml() for child in node.childNodes])
        rev = entry.getElementsByTagName('commit')[0].getAttribute('revision')
        tags[name] = rev
    return tags

@memoize
def listdir(url):
    """
    Returns list of elements in this directory (url)
    e.g. ['trunk/', 'branches/', 'README.txt']
    """
    xml_data = ''.join(runcmd('svn ls --xml %s' % url, log=False, respond=True))
    dom = xml.dom.minidom.parseString(xml_data)
    names = []
    for entry in dom.getElementsByTagName('entry'):
        node = entry.getElementsByTagName('name')[0]
        name = ''.join([child.toxml() for child in node.childNodes])
        names.append(name)
    return name

@memoize
def isdir(url):
    if url[-1]=='/':
        url = url[:-1]
    data = listdir(url)
    if not data:
        # invalid url
        return False
    elif len(data)==1 and data[0]==os.path.basename(url):
        # file
        return False
    else:
        # dir
        return True

@memoize
def has_local_changes(path):
    cmd = 'svn st %s | grep -v ^X | grep -v ^Performing | grep -v ^$' % path
    return len(runcmd(cmd, log=False, respond=True))>0

def update(path):
    """Runs svn up
    """
    cmd = 'svn up'
    return runcmd_unmemoized(cmd, log=True)
