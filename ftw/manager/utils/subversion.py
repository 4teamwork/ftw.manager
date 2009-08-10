"""
contains subversion helper methods
"""

import os
import xml.dom.minidom
from ftw.manager.utils import runcmd, runcmd_with_exitcode
from ftw.manager.utils.memoize import memoize

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
        if not is_subversion(directory):
            raise NotASubversionCheckout
        return ''.join(runcmd('svn info %s | grep URL | cut -d " " -f 2' % directory, log=False, respond=True)).strip()

@memoize
def check_project_layout(directory_or_url, raise_exception=True):
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
    for dir in ('trunk', 'tags', 'branches'):
        if dir not in dircontent:
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
    xml_data = ''.join(runcmd('svn list %s --xml' % tags_dir, log=False, respond=True))
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
    cmd = 'svn list %s' % url
    exitcode, data = runcmd_with_exitcode(cmd, log=False, respond=True)
    if exitcode==0:
        return ''.join(data).strip().split('\n')
    else:
        return None

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
