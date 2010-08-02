from ftw.manager.commands import basecommand
from ftw.manager.utils import output
from ftw.manager.utils import runcmd
from ftw.manager.utils import scm
from ftw.manager.utils.memoize import memoize
import os


class FileSystemRootReached(Exception):
    pass


class I18NDudeBaseCommand(basecommand.BaseCommand):

    def check_conditions(self):
        self.i18ndude = 'i18ndude'
        # we should be in a local repository
        try:
            package_name = scm.get_package_name('.')
            print '  using package name:', package_name
        except scm.NotAScm:
            output.error('Not in a SVN- or GIT-Checkout, unable to guess '
                         'package name', exit=1)
        # get package root
        package_root = scm.get_package_root_path('.')
        print '  using package root path:', package_root
        # check locales directory
        self.locales_dir = os.path.abspath(os.path.join(
                package_root,
                '/'.join(package_name.split('.')),
                'locales',
                ))
        print '  using locales dir:', self.locales_dir
        if not os.path.isdir(self.locales_dir):
            runcmd('mkdir -p %s' % self.locales_dir)

    @property
    @memoize
    def buildout_dir(self):
        path = ['.']
        zopeFound = False
        while not zopeFound:
            dir = os.listdir('/'.join(path))
            if '/' == os.path.abspath('/'.join(path)):
                raise FileSystemRootReached
            elif 'bin' in dir:
                binContents = os.listdir('/'.join(path + ['bin']))
                instances = filter(lambda x: x.startswith('instance') or \
                                       x == 'i18ndude', binContents)
                if len(instances) > 0:
                    zopeFound = True
                else:
                    path.append('..')
            else:
                path.append('..')
        return os.path.abspath('/'.join(path))


class BuildPotCommand(I18NDudeBaseCommand):
    u"""Builds the .pot files in your `locales` directory. By
    default the name of your package is used as i18n domain.
    The locales diretory is expected to be in the root of your
    package (e.g. src/my.package/my/package/locales).

    The .pot files are built with `i18ndude`, which have to be
    installed (ftw.manager as a extras_require). i18ndude will
    search all msgid from the templates and where you use the
    zope message factory.

    """

    command_name = u'i18npot'
    command_shortcut = u'ib'
    description = u'Builds the .pot files in your locales ' +\
        'directory with i18ndude'
    usage = u'ftw %s' % command_name

    def __call__(self):
        scm.tested_for_scms(('svn', 'gitsvn', 'git'), '.')
        scm.require_package_root_cwd()
        self.check_conditions()
        package_name = scm.get_package_name('.')
        if self.options.domain:
            domain = self.options.domain
        else:
            domain = package_name
        package_root = scm.get_package_root_path('.')
        package_dir = os.path.join(package_root, *package_name.split('.'))
        pot_path = os.path.join(self.locales_dir, '%s.pot' % domain)
        output.part_title('Rebuilding pot file at %s' % pot_path)
        # rebuild
        cmd = ['%s rebuild-pot' % self.i18ndude]
        cmd.append('--pot %s' % pot_path)
        # manual file
        manual_file = os.path.join(self.locales_dir, '%s-manual.pot' % domain)
        if os.path.exists(manual_file):
            print '  merging manual pot file:', manual_file
            cmd.append('--merge %s' % manual_file)
        cmd.append('--create %s %s' % (
                domain,
                package_dir,
                ))
        cmd = ' \\\n'.join(cmd)
        runcmd(cmd)

    def register_options(self):
        self.parser.add_option('-d', '--domain', dest='domain',
                               action='store', default=None,
                               help='i18n domain. Default: package name')

basecommand.registerCommand(BuildPotCommand)


class SyncPoCommand(I18NDudeBaseCommand):
    u"""Syncs the .pot files with the .po files of the selected
    language. The files are synced with `i18ndude`, which may
    be installed using the extras_require.

    """
    command_name = u'i18nsync'
    command_shortcut = u'is'
    description = u'Syncs the .pot files with the .po files of a' +\
        'language.'
    usage = u'ftw %s [LANG-CODE]' % command_name

    def __call__(self):
        scm.tested_for_scms(('svn', 'gitsvn', 'git'), '.')
        scm.require_package_root_cwd()
        if len(self.args) < 1:
            output.error('Language code is required', exit=1)
        lang = self.args[0]
        # check
        self.check_conditions()
        package_name = scm.get_package_name('.')
        if self.options.domain:
            domain = self.options.domain
        else:
            domain = package_name
        # check pot file
        pot_path = os.path.join(self.locales_dir, '%s.pot' % domain)
        if not os.path.exists(pot_path):
            output.error('Could not find pot file at: %s' % pot_path, exit=1)
        # check language directory
        lang_dir = os.path.join(self.locales_dir, lang, 'LC_MESSAGES')
        if not os.path.isdir(lang_dir):
            runcmd('mkdir -p %s' % lang_dir)
        # touch po file
        po_file = os.path.join(lang_dir, '%s.po' % domain)
        if not os.path.isfile(po_file):
            runcmd('touch %s' % po_file)
        # sync
        output.part_title('Syncing language "%s"' % lang)
        cmd = '%s sync --pot %s %s' % (
            self.i18ndude,
            pot_path,
            po_file,
            )
        runcmd(cmd)
        # remove language
        output.part_title('Removing language code from po file')
        data = open(po_file).read().split('\n')
        file = open(po_file, 'w')
        for row in data:
            if not row.startswith('"Language-Code') and \
                    not row.startswith('"Language-Name'):
                file.write(row)
                file.write('\n')
        file.close()

    def register_options(self):
        self.parser.add_option('-d', '--domain', dest='domain',
                               action='store', default=None,
                               help='i18n domain. Default: package name')


basecommand.registerCommand(SyncPoCommand)
