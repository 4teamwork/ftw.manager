# -*- coding: utf8 -*-

import os
import basecommand
from ftw.manager.utils import output
from ftw.manager.utils import runcmd
from ftw.manager.utils import scm

class VersionCommand(basecommand.BaseCommand):
    """
    Displays the version of the package you are currently in.
    """

    command_name = 'version'
    description = 'Display Version of the package containing the current directory'

    def __call__(self):
        svn_url = scm.get_svn_url('.').split('/')
        svn_root_url = scm.get_package_root_url('.').split('/')
        package_name = scm.get_package_name('.')
        path = os.path.abspath(os.path.join(
                (len(svn_url) - len(svn_root_url) - 1) * '../',
                package_name.replace('.','/'),
                'version.txt',
        ))
        if not os.path.isfile(path):
            output.error('Could not find file %s' % path, exit=1)
        version = open(path).read().strip()
        print '  Version of %s: %s' % (
            output.ColorString(package_name, output.YELLOW),
            output.ColorString(version, output.YELLOW),
        )

basecommand.registerCommand(VersionCommand)


