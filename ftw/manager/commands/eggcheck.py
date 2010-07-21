from StringIO import StringIO
from ftw.manager.commands.basecommand import BaseCommand, registerCommand
from ftw.manager.utils import output, input, scm, runcmd_with_exitcode, runcmd
from pkg_resources import Requirement
from setuptools import package_index
import distutils.core
import os.path
import re
import sys


WIKI_PYTHON_EGGS = 'http://devwiki.4teamwork.ch/PythonEggs'


class EggCheckCommand(BaseCommand):
    """The command `eggcheck` checks if the egg has some common problems.

    Checks:
    * setup.py
    ** maintainer should be defined
    ** version should be read from version.txt, which sould exist
    ** package namespaces shouls be defined properly (they are usually
    wrong after renaming packages)
    ** various metadata stuff
    """

    command_name = 'eggcheck'
    command_shortcut = 'ec'
    description = 'Check some common problems on a egg'
    usage = 'ftw %s [OPTIONS]' % command_name

    PROBLEM_LEVELS = (
        ('ERROR', output.BOLD_ERROR),
        ('WARNING', output.BOLD_WARNING),
        ('NOTICE', output.WARNING)
        )

    IGNORE_IMPORTS_FROM = (
        'AccessControl',
        'Acquisition',
        'DateTime',
        'ExtensionClass',
        'Missing',
        'MultiMapping',
        'OFS',
        'PIL',
        'Persistence',
        'Products.ATContentTypes',
        'Products.Archetypes',
        'Products.BTreeFolder2',
        'Products.CMFActionIcons',
        'Products.CMFCalendar',
        'Products.CMFCore',
        'Products.CMFDefault',
        'Products.CMFDiffTool',
        'Products.CMFDynamicViewFTI',
        'Products.CMFEditions',
        'Products.CMFFormController',
        'Products.CMFPlacefulWorkflow',
        'Products.CMFPlone',
        'Products.CMFQuickInstallerTool',
        'Products.CMFUid',
        'Products.DCWorkflow',
        'Products.ExtendedPathIndex',
        'Products.ExternalEditor',
        'Products.ExternalMethod',
        'Products.Five',
        'Products.GenericSetup',
        'Products.MIMETools',
        'Products.MailHost',
        'Products.MimetypesRegistry',
        'Products.OFSP',
        'Products.PageTemplates',
        'Products.PasswordResetTool',
        'Products.PlacelessTranslationService',
        'Products.PloneLanguageTool',
        'Products.PlonePAS',
        'Products.PloneTestCase',
        'Products.PluggableAuthService',
        'Products.PluginIndexes',
        'Products.PluginRegistry',
        'Products.PortalTransforms',
        'Products.PythonScripts',
        'Products.ResourceRegistries',
        'Products.Sessions',
        'Products.SiteAccess',
        'Products.SiteErrorLog',
        'Products.StandardCacheManagers',
        'Products.TemporaryFolder',
        'Products.TinyMCE',
        'Products.Transience',
        'Products.ZCTextIndex',
        'Products.ZCatalog',
        'Products.ZGadflyDA',
        'Products.ZODBMountPoint',
        'Products.ZReST',
        'Products.ZSQLMethods',
        'Products.kupu',
        'Products.statusmessages',
        'Record',
        'RestrictedPython',
        'StringIO',
        'Testing.ZopeTestCase',
        'ThreadLock',
        'ZConfig',
        'ZODB3',
        'ZPublisher',
        'Zope2',
        'ZopeUndo',
        'archetypes.kss',
        'archetypes.referencebrowserwidget',
        'borg.localrole',
        'collective.testcaselayer',
        'docutils',
        'five.customerize',
        'five.formlib',
        'five.localsitemanager',
        'initgroups',
        'kss.core',
        'persistent',
        'pkgutil.',
        'plone.app.blob',
        'plone.app.content',
        'plone.app.contentmenu',
        'plone.app.contentrules',
        'plone.app.controlpanel',
        'plone.app.customerize',
        'plone.app.folder',
        'plone.app.form',
        'plone.app.i18n',
        'plone.app.iterate',
        'plone.app.jquerytools',
        'plone.app.kss',
        'plone.app.layout',
        'plone.app.linkintegrity',
        'plone.app.locales',
        'plone.app.openid',
        'plone.app.portlets',
        'plone.app.redirector',
        'plone.app.upgrade',
        'plone.app.users',
        'plone.app.viewletmanager',
        'plone.app.vocabularies',
        'plone.app.workflow',
        'plone.browserlayer',
        'plone.contentrules',
        'plone.fieldsets',
        'plone.i18n',
        'plone.indexer',
        'plone.intelligenttext',
        'plone.locking',
        'plone.memoize',
        'plone.openid',
        'plone.portlet.collection',
        'plone.portlet.static',
        'plone.portlets',
        'plone.protect',
        'plone.session',
        'plone.theme',
        'plonetheme.classic',
        'plonetheme.sunburst',
        'pytz',
        'setuptools',
        'tempstorage',
        'transaction',
        'unittest',
        'wicked',
        'xml.',
        'z3c.autoinclude',
        'zExceptions',
        'zLOG',
        'zdaemon',
        'zope.annotation',
        'zope.app.annotation',
        'zope.app.component',
        'zope.app.container',
        'zope.app.form',
        'zope.app.intid',
        'zope.app.locales',
        'zope.app.pagetemplate',
        'zope.app.publication',
        'zope.app.publisher',
        'zope.app.schema',
        'zope.component',
        'zope.configuration',
        'zope.container',
        'zope.contentprovider',
        'zope.contenttype',
        'zope.deferredimport',
        'zope.deprecation',
        'zope.dottedname',
        'zope.event',
        'zope.exceptions',
        'zope.formlib',
        'zope.i18n',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.lifecycleevent',
        'zope.location',
        'zope.mkzeoinstance',
        'zope.pagetemplate',
        'zope.processlifetime',
        'zope.proxy',
        'zope.publisher',
        'zope.schema',
        'zope.security',
        'zope.sendmail',
        'zope.sequencesort',
        'zope.site',
        'zope.size',
        'zope.structuredtext',
        'zope.tal',
        'zope.tales',
        'zope.testbrowser',
        'zope.testing',
        'zope.traversing',
        'zope.viewlet',
        )

    FIND_LINKS = [
        'http://pypi.python.org/simple',
        'http://downloads.4teamwork.ch/simple',
        'http://psc.4teamwork.ch/simple'
        ]

    def __call__(self):
        """Run the checks
        """
        if not os.path.exists('setup.py'):
            raise Exception('Could not find setup.py')
        if scm.has_local_changes('.'):
            output.error('You have local changes, please commit them first.',
                         exit=True)
        self.check_setup_py()
        self.check_dependencies()

    def register_options(self):
        pass

    @property
    def egginfo(self):
        """Returns a distuls setup instance
        """
        try:
            return self._egg_info
        except AttributeError:
            self._egg_info = distutils.core.run_setup('setup.py')
            return self._egg_info

    def check_setup_py(self):
        """setup.py checks
        """
        # usually run when something has changed. so lets
        # remove our cached egginfo stuff
        try:
            del self._egg_info
        except:
            pass
        self.notify_part('Check setup.py')

        # MAINTAINER
        self.notify_check('Maintainer should be defined')
        maintainer = self.egginfo.get_maintainer()
        if maintainer and maintainer!='UNKNOWN':
            self.notify(True)
        else:
            if len(filter(lambda row:row.startswith('maintainer'),
                          open('setup.py').read().split('\n'))) > 0:
                self.notify(False, 'maintainer is defined as variable but is not used '
                            'in setup call', 'add "maintainer=maintainer," to the setup call', 1)
                if input.prompt_bool('Should I try to fix it?'):
                    rows = open('setup.py').read().split('\n')
                    file_ = open('setup.py', 'w')
                    found = False
                    for i, row in enumerate(rows):
                        file_.write(row)
                        if i != len(rows) - 1:
                            file_.write('\n')
                        if row.strip().startswith('author_email='):
                            file_.write(' ' * 6)
                            file_.write('maintainer=maintainer,')
                            file_.write('\n')
                            found = True
                    file_.close()
                    if not found:
                        output.error('Could not find keyword author_email in your setup.py, '
                                     'you have to fix it manually, sorry.', exit=1)
                    else:
                        self._validate_setup_py()
                        scm.add_and_commit_files('setup.py: register maintainer',
                                                 'setup.py')
                        self.notify_fix_completed()
                    print ''
            else:
                self.notify(False, 'maintainer is not defined in the egg at all',
                            'check %s on how to define a maintainer' % WIKI_PYTHON_EGGS)

        # VERSION.TXT
        self.notify_check('version.txt file exists')
        versiontxt_path = scm.get_package_name('.').replace('.', '/') + '/version.txt'
        if os.path.exists(versiontxt_path) and os.path.isfile(versiontxt_path):
            self.notify(True)
        elif os.path.exists(versiontxt_path):
            self.notify(False, '%s exists but is not a file !?' % versiontxt_path,
                        'it should be a file containing the package version', 0)
        else:
            self.notify(False, '%s does not exist' % versiontxt_path)
            if input.prompt_bool('Should I try to fix it?'):
                version = self.egginfo.get_version()
                file_ = open(versiontxt_path, 'w')
                file_.write(version)
                file_.close()
                scm.add_and_commit_files('Added version.txt file', versiontxt_path)
                self.notify_fix_completed()
                print ''

        # VERSION
        self.notify_check('Version is taken form version.txt')
        rows = open('setup.py').read().split('\n')
        version_rows = filter(lambda row:row.startswith('version ='), rows)
        if len(version_rows) != 1:
            self.notify(False, 'I\'m confused, it seems that you have a mess with '
                        'your versions.',
                        'check %s on how to define versions properly' % WIKI_PYTHON_EGGS)
        elif not version_rows[0].startswith('version = open('):
            self.notify(False, 'I\'m guessing that the version in your setup.py is not '
                        'taken from %s' % versiontxt_path,
                        'check %s on how to define versions properly' % WIKI_PYTHON_EGGS)
            if input.prompt_bool('Should I try to fix it?'):
                new_version_row = "version = open('%s').read().strip()" % versiontxt_path
                rows[rows.index(version_rows[0])] = new_version_row
                file_ = open('setup.py', 'w')
                file_.write('\n'.join(rows))
                file_.close()
                self._validate_setup_py()
                scm.add_and_commit_files('setup.py: using version.txt', 'setup.py')
                self.notify_fix_completed()
        else:
            self.notify(True)

        # NAMESPACES
        self.notify_check('Check namespaces')
        guessed_namespaces = []
        namespace_parts = scm.get_package_name('.').split('.')
        for i, space in enumerate(namespace_parts[:-1]):
            guessed_namespaces.append('.'.join(namespace_parts[:i+1]))
        if set(guessed_namespaces) == set(self.egginfo.namespace_packages):
            self.notify(True)
        else:
            print '  current namespaces: ', str(self.egginfo.namespace_packages)
            print '  expected namespaces:', str(guessed_namespaces)
            print '  package name:       ', scm.get_package_name('.')
            self.notify(False, 'I think your namespace_packages declaration is wrong')
            if input.prompt_bool('Should I try to fix it?'):
                guessed_namespaces.sort()
                rows = open('setup.py').read().split('\n')
                nsrows = filter(lambda x:x.strip().startswith('namespace_packages'), rows)
                if len(nsrows) != 1:
                    output.error('Could not fix it: expected one and only one line '
                                 'beginning with "namespace_packages" in setup.py..',
                                 exit=True)
                else:
                    new_row = nsrows[0].split('=')[0] + '=' + str(guessed_namespaces) + ','
                    rows[rows.index(nsrows[0])] = new_row
                    file_ = open('setup.py', 'w')
                    file_.write('\n'.join(rows))
                    file_.close()
                    self._validate_setup_py()
                    scm.add_and_commit_files('setup.py: fixed namespace_packages',
                                             'setup.py')
                    self.notify_fix_completed()

        # VARIOUS CHECKS
        self.notify_check('Various setup.py checks')
        failure = False

        # .. name
        if self.egginfo.get_name() != scm.get_package_name('.'):
            failure = True
            self.notify(False, 'Name: Expected name in setup.py to be ' + \
                            '"%s" ' % scm.get_package_name('.') + \
                            'but it was "%s"' % self.egginfo.get_name())

        # maintainer in description
        if self.egginfo.get_maintainer() not in self.egginfo.get_description():
            failure = True
            self.notify(False, 'Description: Maintainer is not defined in description',
                        'Check out %s' % WIKI_PYTHON_EGGS, 2)

        # author: use maintainer
        expected_author = '%s, 4teamwork GmbH' % self.egginfo.get_maintainer()
        if self.egginfo.get_author() != expected_author:
            failure = True
            self.notify(False, 'Author: Expected author to be "%s""' % expected_author + \
                        ' but it is "%s"' % self.egginfo.get_author(),
                        'Check out %s' % WIKI_PYTHON_EGGS, 2)

        # author email
        if self.egginfo.get_author_email() != 'mailto:info@4teamwork.ch':
            failure = True
            self.notify(False, 'Author email: the email should be'
                        ' "mailto:info@4teamwork.ch"',
                        'Check out %s' % WIKI_PYTHON_EGGS, 2)

        # license
        if self.egginfo.get_license() != 'GPL2':
            failure = True
            self.notify(False, 'License: the license should be "GPL2"',
                        'Check out %s' % WIKI_PYTHON_EGGS, 2)

        # .. ok?
        if not failure:
            self.notify(True)

    def check_dependencies(self):
        """ Checks, if there are missing dependencies
        """
        self.notify_part('Check dependencies')
        # get current requires
        requires = self.egginfo.install_requires

        # extend it with extra requires
        if self.egginfo.extras_require:
            for ename, erequires in self.egginfo.extras_require.items():
                requires.extend(erequires)

        print ' current requirements (including extras):'
        for egg in requires:
            print '    -', egg
        print ''

        # add the requirements without extras too
        for egg in requires[:]:
            if '[' in egg:
                requires.append(egg.split('[')[0])

        self.notify_check('Check imports on python files and zcml stuff')
        propose_requires = []

        # contains ipath:file mapping of python and zcml imports
        ipath_file_mapping = {}

        # SEARCH PYTHON FILES
        # make a grep on python files
        py_grep_results = runcmd("find . -name '*.py' -exec grep -Hr 'import ' {} \;",
                                 respond=True)
        # cleanup:
        # - strip rows
        # - remove the rows with spaces (they are not realle imports)
        # - remove "as xxx"
        py_grep_results = filter(lambda row: ' ' in row,
                                 [row.strip().split(' as ')[0] for row in py_grep_results])

        for row in py_grep_results:
            file_, statement = row.split(':')
            # make a import path
            ipath = statement.replace('from ', '').replace(' import ',
                                                           '.').replace('import', '').strip()
            ipath = ipath.replace('...', '').replace('>>>', '')
            ipath_parts = ipath.split('.')

            if '#' in ipath:
                continue

            # ignore namespace imports (python internals etc)
            if len(ipath_parts) == 1:
                continue

            ipath_file_mapping[ipath] = file_

        # SEARCH ZCML FILES
        cmd = "find . -name '*.zcml' -exec grep -Hr '\(layer\|for\)=' {} \;"
        zcml_grep_results = runcmd(cmd, respond=True)

        # cleanup results
        zcml_xpr = re.compile('(for|layer)="(.*?)("|$)')
        for row in zcml_grep_results:
            file_, stmt = row.split(':')
            stmt = stmt.strip()
            match = zcml_xpr.search(stmt)
            if not match:
                # maybe we have a more complicated statement (e.g. multiline)
                break
            ipath = match.groups()[1].strip()

            ipath = ipath.replace('*', '').strip()

            if '#' in ipath:
                continue

            if not ipath.startswith('.'):
                ipath_file_mapping[ipath] = file_


        # HANDLE ALL IMPORTS
        for ipath, file_ in ipath_file_mapping.items():
            ipath_parts = ipath.split('.')
            # ignore local imports
            if ipath.startswith(scm.get_package_name('.')):
                continue

            # is it already required?
            found = False
            for egg in requires:
                if ipath.startswith(egg):
                    found = True
                    break
            if not found:
                # is it already proposed?
                for egg in propose_requires:
                    if ipath.startswith(egg):
                        found = True
                        break
            if not found:
                # is it ignored?
                for egg in self.IGNORE_IMPORTS_FROM:
                    if ipath.startswith(egg):
                        found = True
                        break
            if found:
                continue

            # maybe we have a module which import relatively
            module_path = os.path.join(os.path.dirname(file_),
                                       ipath_parts[0])
            if os.path.isfile(module_path + '.py') or \
                    os.path.isfile(module_path + '/__init__.py'):
                continue

            # start on level 2 and for searching egg
            guessed_egg_names = ['.'.join(ipath_parts[:i])
                                 for i, part in enumerate(ipath_parts)
                                 if i > 1]

            # does one of the eggs exist?
            found = False

            # .. in pypi
            for egg_name in guessed_egg_names:
                if len(self.find_egg_in_index(egg_name)) > 0:
                    if egg_name.strip() not in propose_requires:
                        propose_requires.append(egg_name.strip())
                    found = True
                    break

            # .. or do we have one in the svn cache?
            if not found:
                for egg_name in guessed_egg_names:
                    if scm.guess_package_url(egg_name):
                        if egg_name.strip() not in propose_requires:
                            propose_requires.append(egg_name.strip())
                        found = True
                        break

            if not found:
                print '  ', output.colorize(ipath, output.INFO), 'in', \
                    output.colorize(file_, output.INFO), \
                    output.colorize('is not covered by requirements '
                                    'and I could find a egg with such a name',
                                    output.WARNING)

        if scm.get_package_name('.') in propose_requires:
            propose_requires.remove(scm.get_package_name('.'))

        if len(propose_requires)==0:
            self.notify(True)
            return
        propose_requires.sort()
        print ''
        print '  There are some requirements missing. I propose to add these:'
        for egg in propose_requires:
            print '   ', egg
        print ''

        # try to add them automatically:
        if input.prompt_bool('Should I try to add them?'):
            rows = open('setup.py').read().split('\n')
            # find "install_requires"
            frows = filter(lambda row:row.strip().startswith('install_requires='),
                           rows)
            if len(frows) != 1:
                output.error('Somethings wrong with your setup.py: expected only '
                             'one row containing "install_requires=", but '
                             'got %i' % len(frows), exit=1)
            insert_at = rows.index(frows[0]) + 1
            for egg in propose_requires:
                rows.insert(insert_at, ' ' * 8 + "'%s'," % egg)
            file_ = open('setup.py', 'w')
            file_.write('\n'.join(rows))
            file_.close()
            self._validate_setup_py()
            scm.add_and_commit_files('setup.py: added missing dependencies',
                                     'setup.py')
            self.notify_fix_completed()

    def find_egg_in_index(self, pkg):
        # There is a problem when using find-links for eggs which are on the pypi
        # so we need to use two different indexes
        # - self.pi : index using find-links
        try:
            self.pi
        except AttributeError:
            self.pi = package_index.PackageIndex()
            self.pi.add_find_links(self.FIND_LINKS)
        # - self.pypi : index only for pypi
        try:
            self.pypi
        except AttributeError:
            self.pypi = package_index.PackageIndex()

        # first we try it using find-links
        index = self.pi
        req = Requirement.parse(pkg)
        index.package_pages[req.key] = self.FIND_LINKS
        # supress the find_packages output ...
        try:
            ori_stdout = sys.stdout
            sys.stdout = StringIO()
            try:
                index.find_packages(req)
            except TypeError:
                # .. that didnt work, so lets try it without find-links.. we need to
                # use the "fresh" self.pypi index
                index = self.pypi
                index.find_packages(req)
        except:
            sys.stdout = ori_stdout
        else:
            sys.stdout = ori_stdout
        return index[req.key]

    def notify_part(self, part_title):
        """Print a part heading to the stdout
        """
        print ''
        output.part_title(part_title)
        print ''

    def notify_check(self, title):
        """Print check-title to the stdout
        """
        print output.colorize('CHECK:', output.BOLD_INFO), \
            output.colorize(title, output.INFO)

    def notify(self, state, problem='', solution='', problem_level=0):
        """Notify the user of a problem
        """
        if state:
            print '  OK'
        else:
            prob_type, prob_color = self.PROBLEM_LEVELS[problem_level]
            print ' ', output.colorize(prob_type, prob_color), \
                output.colorize(problem, prob_color)
            if solution:
                print '  SOLUTION:', solution
        print ''

    def notify_fix_completed(self):
        print output.colorize('Fix completed successfully', output.INFO)
        print ''

    def _validate_setup_py(self, respond=True, respond_error=True):
        """Runs the egg_info command on the ./setup.py for checking if it still
        works.

        """
        cmd = '%s setup.py egg_info' % sys.executable
        return runcmd_with_exitcode(cmd, respond=respond,
                                    respond_error=respond_error)

registerCommand(EggCheckCommand)
