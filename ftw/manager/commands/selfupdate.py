# -*- coding: utf-8 -*-

from ftw.manager.commands import basecommand


class SelfUpdate(basecommand.BaseCommand):
    """
    Updates ftw.manager to the newest version from PSC using easy_install
    Uses PSC-URL: http://downloads.4teamwork.ch/4teamwork/ftw/simple
    """

    command_name = 'selfupdate'
    description = 'Updates ftw.manager with newest version from PSC using easy_install'
    usage = 'ftw %s [options]' % command_name

    def __call__(self):
        from pkg_resources import load_entry_point
        easy_install = load_entry_point('setuptools==0.6c9', 'console_scripts', 'easy_install')
        easy_install(['-U', '-f', self.options.findLinks, 'ftw.manager'])

    def register_options(self):
        default_psc_url = 'http://downloads.4teamwork.ch/4teamwork/ftw/simple'
        self.parser.add_option('-f', '--find-links', dest='findLinks',
                               action='store', type='string', default=default_psc_url,
                               help='additional URL(s) to search for packages')


basecommand.registerCommand(SelfUpdate)

