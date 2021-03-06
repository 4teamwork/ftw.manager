from StringIO import StringIO
from ftw.manager.packages import PACKAGE_REQUIREMENTS_INADVISABLE
from ftw.manager.packages import TESTING_PACKAGES
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
    u"""
    The command `eggcheck` checks if the egg has some common problems.

    Checks:
    * setup.py
    ** maintainer should be defined
    ** version should be read from version.txt, which sould exist
    ** package namespaces shouls be defined properly
    ** various metadata stuff (name, description, author, email, license)
    ** the docs/HISTORY.txt file should be embedded
    ** we should be able to run `setup.py egg_info`
    * install_requires is checked by parsing all imports and some zcml
    * the long_description in setup.py (and included files) should be rEST
    * various paster problems are checked
    ** do not use CHANGES.txt or CONTRIBUTORS.txt
    ** do not use interfaces as folder
    ** viewlets and portlets should not be within a browser directory
    ** setup.cfg should not exist

    """

    command_name = u'eggcheck'
    command_shortcut = u'ec'
    description = u'Check some common problems on a egg'
    usage = u'ftw %s [OPTIONS]' % command_name

    PROBLEM_LEVELS = (
        ('ERROR', output.BOLD_ERROR),
        ('WARNING', output.BOLD_WARNING),
        ('NOTICE', output.WARNING),
        )

    FIND_LINKS = [
        'http://pypi.python.org/simple',
        'http://downloads.4teamwork.ch/simple',
        'http://psc.4teamwork.ch/simple',
        ]

    def register_options(self):
        self.parser.add_option('-s', '--check-setup', default=False,
                               action='store_true', dest='check_setup',
                               help='Check basic stuff in setup.py (maintainer'
                               ', version, etc)')
        self.parser.add_option('-p', '--check-paster', default=False,
                               action='store_true', dest='check_paster',
                               help='Check problems caused by paster')
        self.parser.add_option('-d', '--check-description', default=False,
                               action='store_true', dest='check_description',
                               help='Checks the long description / validates '
                               'rEST')
        self.parser.add_option('-r', '--check-requires', default=False,
                               action='store_true', dest='check_requires',
                               help='Check install_requires: search all python'
                               ' imports'
                               ' and zcml directives')
        self.parser.add_option('-z', '--check-zcml', default=False,
                               action='store_true', dest='check_zcml',
                               help='ZCML checks (locales registration, ...)')

    def __call__(self):
        """Run the checks
        """
        scm.tested_for_scms(('svn', 'gitsvn', 'git'), '.')
        if not os.path.exists('setup.py'):
            raise Exception('Could not find setup.py')
        if scm.has_local_changes('.'):
            output.error('You have local changes, please commit them first.',
                         exit=True)

        self.checks = []

        all_checks = []
        # get all checks from parser
        for option in self.parser.option_list:
            # get all options with a dest= starting with check_
            if option.dest and option.dest.startswith('check_'):
                opt_value = getattr(self.options, option.dest)
                short_name = option.dest[len('check_'):]
                if opt_value:
                    self.checks.append(short_name)
                all_checks.append(short_name)

        # if there are no checks activated by parementer, activate all
        if not len(self.checks):
            self.checks = all_checks

        # run the checks
        if 'setup' in self.checks:
            self.check_setup_py()
        if 'paster' in self.checks:
            self.check_paster_stuff()
        if 'description' in self.checks:
            self.check_description()
        if 'requires' in self.checks:
            self.check_requires()
        if 'zcml' in self.checks:
            self.check_zcml()

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
        self.notify_part('Check setup.py')

        # MAINTAINER
        self.notify_check('Maintainer should be defined')
        maintainer = self.egginfo.get_maintainer()
        if maintainer and maintainer != 'UNKNOWN':
            self.notify(True)
        else:
            if len(filter(lambda row: row.startswith('maintainer'),
                          open('setup.py').read().split('\n'))) > 0:
                self.notify(False, 'maintainer is defined as variable but is '
                            'not used in setup call',
                            'add "maintainer=maintainer," to the setup call',
                            1, pause=False)
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
                        output.error('Could not find keyword author_email in '
                                     'your setup.py, you have to fix it '
                                     'manually, sorry.', exit=1)
                    else:
                        self._validate_setup_py()
                        scm.add_and_commit_files(
                            'setup.py: register maintainer',
                            'setup.py')
                        self.notify_fix_completed()
                    print ''
            else:
                self.notify(False,
                            'maintainer is not defined in the egg at all',
                            'check %s on how to define a maintainer' % \
                                WIKI_PYTHON_EGGS)

        # VERSION.TXT
        self.notify_check('version.txt file exists')
        versiontxt_path = scm.get_package_name('.').replace('.', '/') + \
            '/version.txt'
        if os.path.exists(versiontxt_path) and os.path.isfile(versiontxt_path):
            self.notify(True)
        elif os.path.exists(versiontxt_path):
            self.notify(False, '%s exists but is not a file !?' % \
                            versiontxt_path,
                        'it should be a file containing the package version',
                        0)
        else:
            self.notify(False, '%s does not exist' % versiontxt_path,
                        pause=False)
            if input.prompt_bool('Should I try to fix it?'):
                version = self.egginfo.get_version()
                file_ = open(versiontxt_path, 'w')
                file_.write(version)
                file_.close()
                scm.add_and_commit_files('Added version.txt file',
                                         versiontxt_path)
                self.notify_fix_completed()
                print ''

        # VERSION
        self.notify_check('Version is taken form version.txt')
        rows = open('setup.py').read().split('\n')
        version_rows = filter(lambda row: row.startswith('version ='), rows)
        if len(version_rows) != 1:
            self.notify(False, 'I\'m confused, it seems that you have a mess '
                        'with your versions.',
                        'check %s on how to define versions properly' % \
                            WIKI_PYTHON_EGGS)
        elif not version_rows[0].startswith('version = open('):
            self.notify(False, 'I\'m guessing that the version in your '
                        'setup.py is not taken from %s' % versiontxt_path,
                        'check %s on how to define versions properly' % \
                            WIKI_PYTHON_EGGS, pause=False)
            if input.prompt_bool('Should I try to fix it?'):
                new_version_row = "version = open('%s').read().strip()" % \
                    versiontxt_path
                rows[rows.index(version_rows[0])] = new_version_row
                file_ = open('setup.py', 'w')
                file_.write('\n'.join(rows))
                file_.close()
                self._validate_setup_py()
                scm.add_and_commit_files('setup.py: using version.txt',
                                         'setup.py')
                self.notify_fix_completed()
        else:
            self.notify(True)

        # NAMESPACES
        self.notify_check('Check namespaces')
        guessed_namespaces = []
        namespace_parts = scm.get_package_name('.').split('.')
        for i, space in enumerate(namespace_parts[:-1]):
            guessed_namespaces.append('.'.join(namespace_parts[:i + 1]))
        if set(guessed_namespaces) == set(self.egginfo.namespace_packages):
            self.notify(True)
        else:
            print '  current namespaces: ', str(
                self.egginfo.namespace_packages)
            print '  expected namespaces:', str(guessed_namespaces)
            print '  package name:       ', scm.get_package_name('.')
            self.notify(False, 'I think your namespace_packages declaration '
                        'is wrong', pause=False)
            if input.prompt_bool('Should I try to fix it?'):
                guessed_namespaces.sort()
                rows = open('setup.py').read().split('\n')
                nsrows = filter(lambda x:
                                    x.strip().startswith('namespace_packages'),
                                rows)
                if len(nsrows) != 1:
                    output.error('Could not fix it: expected one and only one'
                                 ' line beginning with "namespace_packages"'
                                 ' in setup.py..',
                                 exit=True)
                else:
                    new_row = nsrows[0].split('=')[0] + '=' + \
                        str(guessed_namespaces) + ','
                    rows[rows.index(nsrows[0])] = new_row
                    file_ = open('setup.py', 'w')
                    file_.write('\n'.join(rows))
                    file_.close()
                    self._validate_setup_py()
                    scm.add_and_commit_files(
                        'setup.py: fixed namespace_packages', 'setup.py')
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
            self.notify(False, 'Description: Maintainer is not defined '
                        'in description',
                        'Check out %s' % WIKI_PYTHON_EGGS, 2)

        # docs/HISTORY.txt
        setuppy = open('setup.py').read()
        if 'HISTORY.txt' not in setuppy or \
                not os.path.exists('docs/HISTORY.txt') or \
                open('docs/HISTORY.txt').read() not in \
                self.egginfo.get_long_description():
            self.notify(False, 'docs/HISTORY.txt embedded be used in '
                        'long_description',
                        'Check long_description on %s' % WIKI_PYTHON_EGGS)

        # author: use maintainer
        expected_author = '%s, 4teamwork GmbH' % self.egginfo.get_maintainer()
        if self.egginfo.get_author() != expected_author:
            failure = True
            self.notify(False, 'Author: Expected author to be "%s""' % \
                            expected_author + \
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

        # run egg_info
        self.notify_check('we should be able to run `setup.py egg_info`')
        state, out, errors = self._validate_setup_py()
        if out:
            print '   ', out.replace('\n', '\n    ')
        if errors:
            print '   ', errors.replace('\n', '\n    ')
        if state == 0:
            self.notify(True)
        else:
            state.notify(False, 'Cant run `python setup.py egg_info`, see '
                         'errors above', 0)

    def check_paster_stuff(self):
        """ Paster does some bad things, so lets fix them.
        """
        self.notify_part('Check paster problems')
        setuppy = open('setup.py').read()
        package_base_path = scm.get_package_name('.').replace('.', '/')

        # CHANGES.txt
        self.notify_check('CHANGES.txt should not be used')
        changes_used = False
        if 'CHANGES.txt' in setuppy:
            self.notify(False, 'CHANGES.txt is used in setup.py somehow',
                        'Fix setup.py: remove the CHANGES.txt stuff', 1)
            changes_used = True
        if os.path.exists('CHANGES.txt'):
            self.notify(False, 'A ./CHANGES.txt exists',
                        'Remove the CHANGES.txt, we use the docs/HISTORY.txt',
                        1, pause=changes_used)
            if not changes_used:
                if input.prompt_bool(
                    'Should I remove the CHANGES.txt for you?'):
                    scm.remove_files('CHANGES.txt')
                    scm.commit_files('Removed unused CHANGES.txt',
                                     'CHANGES.txt')
                    self.notify_fix_completed()
        elif not changes_used:
            self.notify(True)

        # CONTRIBUTORS.txt
        self.notify_check('CONTRIBUTORS.txt should not be used')
        contributors_used = False
        if 'CONTRIBUTORS.txt' in setuppy:
            self.notify(False, 'CONTRIBUTORS.txt is used in setup.py somehow',
                        'Fix setup.py: remove the CONTRIBUTORS.txt stuff', 1)
            contributors_used = True
        if os.path.exists('CONTRIBUTORS.txt'):
            self.notify(False, 'A ./CONTRIBUTORS.txt exists',
                        'Remove the CONTRIBUTORS.txt', 1, pause=False)
            if not contributors_used:
                if input.prompt_bool('Should I remove the CONTRIBUTORS.txt '
                                     'for you?'):
                    scm.remove_files('CONTRIBUTORS.txt')
                    scm.commit_files('Removed unused CONTRIBUTORS.txt',
                                     'CONTRIBUTORS.txt')
                    self.notify_fix_completed()
        elif not contributors_used:
            self.notify(True)

        # interfaces not as folder
        self.notify_check('%s.interfaces should not be a folder' %
                          scm.get_package_name('.'))
        path = os.path.join(package_base_path, 'interfaces')
        if os.path.isdir(path):
            self.notify(False, '%s is a folder' % path,
                        'Use a interfaces.py, not a interfaces folder', 2)
        else:
            self.notify(True)

        # viewlets / portlets
        self.notify_check('Portlets and viewlets folders')
        dirs = ('viewlets', 'portlets')
        all_ok = True
        for dir in dirs:
            bad_path = os.path.join(package_base_path, 'browser', dir)
            good_path = os.path.join(package_base_path, dir)
            if os.path.exists(bad_path):
                all_ok = False
                self.notify(False, 'Directory exists at: %s' % bad_path,
                            'Move it to %s' % good_path, 2)
        if all_ok:
            self.notify(True)

        # setup.cfg
        self.notify_check('Do not use setup.cfg')
        if os.path.exists('setup.cfg'):
            self.notify(False, 'Found a setup.cfg', 'Remove the setup.cfg', 1,
                        pause=False)
            if input.prompt_bool('Should I remove the setup.cfg?'):
                scm.remove_files('setup.cfg')
                scm.commit_files('Removed setup.cfg', 'setup.cfg')
                self.notify_fix_completed()
        else:
            self.notify(True)

    def check_description(self):
        """ Validates the restructured text of the long_description and
        included files

        """
        self.notify_part('Check the long_description')
        self.notify_check('long_description should be restructured text')
        cmd = '%s setup.py check --restructuredtext --strict' % sys.executable
        if runcmd_with_exitcode(cmd, log=0) == 0:
            self.notify(True)
        else:
            self.notify(False, 'You have restructured text errors in your long_description.',
                        'Run "ftw checkdocs" for detailed errors.', 0)

    def _get_guessed_related_packages(self):
        """If we are in e.g. src/my.package, it will return a list
        of other folders in the src folder.

        """
        path = os.getcwd().split('/')
        if path[-2] == 'src':
            other_dirs = filter(
                lambda e: os.path.isdir('../' + e) and e != path[-1],
                os.listdir('..'))
            return tuple(other_dirs)
        else:
            return ()

    def check_requires(self):
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

        self.notify_check('Its not necessary to import some default plone / zope stuff')
        failures = False
        for egg in requires:
            if egg in PACKAGE_REQUIREMENTS_INADVISABLE and egg not in TESTING_PACKAGES:
                self.notify(False, 'Maybe you should remove the requirement ' +\
                                output.colorize(egg, output.ERROR) +\
                                output.colorize('. It seems to be in a python, ' +\
                                                    'zope or plone distribution and ' +\
                                                    'those packages should not be ' +\
                                                    'set as requirement.', output.WARNING),
                            problem_level=2)
                failures = True
        if not failures:
            self.notify(True)

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
        cmd = "find . -name '*.zcml' -exec grep -Hr '\(layer\|package\|for\)=' {} \;"
        zcml_grep_results = runcmd(cmd, respond=True)

        # cleanup results
        zcml_xpr = re.compile('(for|layer)="(.*?)("|$)')
        for row in zcml_grep_results:
            file_, stmt = row.split(':', 1)
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

        # for later use
        guessed_related_packages = self._get_guessed_related_packages()

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
                for egg in PACKAGE_REQUIREMENTS_INADVISABLE + TESTING_PACKAGES:
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

            # is there package in our src directory, if we are in one?
            for egg_name in guessed_egg_names:
                if egg_name.strip() in guessed_related_packages:
                    if egg_name.strip() not in propose_requires:
                        propose_requires.append(egg_name.strip())
                    found = True
                    break

            # .. in pypi
            if not found:
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

    def check_zcml(self):
        """ ZCML Checks:
        - locales registration

        """
        self.notify_part('ZCML checks')

        locales_directories = []
        # locations
        self.notify_check('Location of locales directory')
        failed = False
        pkg_root_path = './%s' % scm.get_package_name('.').replace('.', '/')
        for dirpath, dirnames, filenames in os.walk('.'):
            if 'locales' in dirnames:
                locales_directories.append((dirpath, 'locales'))
                if dirpath != pkg_root_path:
                    failed = True
                    self.notify(False, 'Found locales-directory in suspicious location: '
                                '%s/locales' % dirpath,
                                'Expected locales directory in %s' % pkg_root_path, 2)
        if not failed:
            self.notify(True)

        # registration
        self.notify_check('Check registration of locales dirs')
        failed = False
        for dirpath, dirname in locales_directories:
            zcmlpath = os.path.join(dirpath, 'configure.zcml')
            if not os.path.exists(zcmlpath):
                self.notify(False, 'Could not find zcml file at %s' % zcmlpath)
                failed = True
            elif '"%s"' % dirname not in open(zcmlpath).read():
                self.notify(False, '%s/%s seems not to be registered in ' % (
                        dirpath, dirname, zcmlpath))
        if not failed:
            self.notify(True)


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

    def notify(self, state, problem='', solution='', problem_level=0,
               pause=True):
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
            if pause:
                input.prompt('[ENTER TO CONTINUE]')
        print ''

    def notify_fix_completed(self):
        print output.colorize('Fix completed successfully', output.INFO)
        print ''

    def _validate_setup_py(self, respond=True, respond_error=True):
        """Runs the egg_info command on the ./setup.py for checking if it still
        works.

        """
        # usually run when something has changed. so lets
        # remove our cached egginfo stuff
        try:
            del self._egg_info
        except:
            pass
        cmd = '%s setup.py egg_info' % sys.executable
        return runcmd_with_exitcode(cmd, respond=respond,
                                    respond_error=respond_error)

registerCommand(EggCheckCommand)
