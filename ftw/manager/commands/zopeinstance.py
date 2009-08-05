
import basecommand

class ZopeInstanceCommand(basecommand.BaseCommand):
    """
    Run bin/instance from any directory within the buildout.
    This may be useful called from a editor (e.g. vim).
    """

    command_name = 'zopeinstance'
    command_shortcut = 'zi'
    description = 'Run bin/instance placeless'
    usage = '%%prog %s action [options]' % command_name

    def __call__(self):
        raise NotImplemented

basecommand.registerCommand(ZopeInstanceCommand)

