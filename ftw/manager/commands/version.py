# -*- coding: utf-8 -*-

from ftw.manager.utils import output
from ftw.manager.utils import scm
import basecommand
import os


class VersionCommand(basecommand.BaseCommand):
    """
    Displays the version of the package you are currently in.
    """

    command_name = 'version'
    description = 'Display Version of the package containing the current ' +\
        'directory'
    usage = 'ftw %s' % command_name

    def __call__(self):
        scm.tested_for_scms(('svn', 'gitsvn'), '.')
        svn_url = scm.get_svn_url('.').split('/')
        svn_root_url = scm.get_package_root_url('.').split('/')
        package_name = scm.get_package_name('.')
        path = os.path.abspath(os.path.join(
                (len(svn_url) - len(svn_root_url) - 1) * '../',
                package_name.replace('.', '/'),
                'version.txt',
        ))
        if not os.path.isfile(path):
            output.error('Could not find file %s' % path, exit=1)
        version = open(path).read().strip()
        print '  Version of %s: %s' % (
            output.colorize(package_name, output.WARNING),
            output.colorize(version, output.WARNING),
        )

basecommand.registerCommand(VersionCommand)
