
import os
import sys
import basecommand
from ftw.manager.utils.output import error
from ftw.manager.utils import runcmd

class ZopeInstanceCommand(basecommand.BaseCommand):
    """
    Run bin/instance from any directory within the buildout.
    This may be useful called from a editor (e.g. vim).

    Example:
        % ftw zi fg
    """

    command_name = 'zopeinstance'
    command_shortcut = 'zi'
    description = 'Run bin/instance placeless'
    usage = 'ftw %s action [options]' % command_name
    use_optparse = False

    def __call__(self):
        path = ['.']
        zopeFound = False
        instance = []
        while not zopeFound:
            dir = os.listdir('/'.join(path))
            if '/'==os.path.abspath('/'.join(path)):
                error('File system root reached: no zope instance found ..', exit=True)
            elif 'bin' in dir:
                binContents = os.listdir('/'.join(path+['bin']))
                instances = filter(lambda x:x.startswith('instance'), binContents)
                if len(instances)>0:
                    zopeFound = True
                else:
                    path.append('..')
            else:
                path.append('..')
        p = os.path.abspath('/'.join(path + ['bin', instances[0]]))
        cmd = '%s %s' % (p, ' '.join(sys.argv[2:]))
        runcmd(cmd, log=True)

basecommand.registerCommand(ZopeInstanceCommand)


