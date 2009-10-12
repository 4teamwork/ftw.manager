# -*- coding: utf8 -*-

import os

from ftw.manager.commands import basecommand
from ftw.manager.config import Configuration
from ftw.manager.utils import input
from ftw.manager.utils import output
from ftw.manager.schemes import COLOR_SCHEMES

class Setup(basecommand.BaseCommand):
    """
    Setup the ftw.manager command.
    Creates a config file in $HOME/.ftw.manager/config
    """

    command_name = 'setup'
    description = 'Configuration Wizard for ftw.manager'
    usage = 'ftw %s' % command_name

    def __call__(self):
        output.part_title('Configure ftw.manager')
        # get config path
        config = Configuration()
        config.initialize_configuration()
        # ask some questions
        syntax = input.prompt_bool('Enable color highlighting?', default=True)
        config.config.set('output', 'syntax', syntax)
        if syntax:
            # ask for scheme
            schemes = COLOR_SCHEMES.keys()
            current_scheme = config.color_scheme or 'light'
            def validator(value):
                return value.lower() in schemes+[''] and 1 or 'Select one of: %s' % ', '.join(schemes)
            print ' * Which color scheme would you like to use?'
            for s in schemes:
                print '   *', s
            scheme = input.prompt('Select color scheme [%s]:' %
                    '/'.join([s==current_scheme and s.upper() or s for s in schemes]), validator).lower()
            if not scheme:
                scheme = current_scheme
            config.config.set('output', 'scheme', scheme)
        # and save
        config.write_config()


basecommand.registerCommand(Setup)

