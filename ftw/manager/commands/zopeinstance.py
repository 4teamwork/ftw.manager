from ftw.manager.utils import runcmd
from ftw.manager.utils.output import error
import basecommand
import os
import sys


class ZopeInstanceCommand(basecommand.BaseCommand):
    u"""
    Run bin/instance from any directory within the buildout.
    This may be useful called from a editor (e.g. vim).

    Example:
    % ftw zi fg

    """

    command_name = u'zopeinstance'
    command_shortcut = u'zi'
    description = u'Run bin/instance placeless'
    usage = u'ftw %s action [options]' % command_name
    use_optparse = False

    def __call__(self):
        path = ['.']
        zopeFound = False
        while not zopeFound:
            dir = os.listdir('/'.join(path))
            if '/' == os.path.abspath('/'.join(path)):
                error('File system root reached: no zope instance found ..',
                      exit=True)
            elif 'bin' in dir:
                binContents = os.listdir('/'.join(path + ['bin']))
                instances = filter(lambda x: x.startswith('instance'),
                                   binContents)
                if len(instances) > 0:
                    zopeFound = True
                else:
                    path.append('..')
            else:
                path.append('..')
        p = os.path.abspath('/'.join(path + ['bin', instances[0]]))
        cmd = '%s %s' % (p, ' '.join(sys.argv[2:]))
        runcmd(cmd, log=True)

basecommand.registerCommand(ZopeInstanceCommand)
