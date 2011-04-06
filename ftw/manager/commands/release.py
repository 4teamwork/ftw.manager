from ftw.manager.commands import basecommand
from ftw.manager.utils import git
from ftw.manager.utils import input
from ftw.manager.utils import output
from ftw.manager.utils import runcmd
from ftw.manager.utils import runcmd_with_exitcode
from ftw.manager.utils import scm
from ftw.manager.utils import subversion as svn
import ConfigParser
import os
import sys


class ReleaseCommand(basecommand.BaseCommand):
    u"""
    This command creates a source release and publishs it on pypi
    or a closed egg repository like a PSC.

    For releasing problerly you need to configure the credentials to
    your target in your `./pypirc`.

    Following tasks will be performed:

    * Create a tag
    * Change versions in tag and trunk
    * Fix HISTORY.txt in tag and trunk
    * Create a source dist of the new tag
    * Upload the dist to the selected target

    More info on how to make release: https://devwiki.4teamwork.ch/Releasen

    """

    command_name = u'release'
    command_shortcut = u'rl'
    description = u'Release eines Packets erstellen'
    usage = u'ftw %s [OPTIONS]' % command_name

    def register_options(self):
        self.parser.add_option('-e', '--only-egg', dest='release_egg_only',
                               action='store_true', default=False,
                               help='Do not commit changes (no tag, no '
                               'versions changed), just create / submit'
                               ' the source distribution.')
        self.parser.add_option('-E', '--no-egg', dest='release_egg',
                               action='store_false', default=True,
                               help='Do not create / submit the dist, but '
                               'create a tag and change the bump versions.')
        self.parser.add_option('-i', '--ignore-doc-errors',
                               dest='ignore_doc_errors',
                               action='store_true', default=False,
                               help='Do not check if the description is '
                               'valid restructured text.')

    def __call__(self):
        scm.tested_for_scms(('svn', 'gitsvn', 'git'), '.')
        self.check_doc()
        self.analyse()
        if self.options.release_egg:
            self.check_pyprc()
        if not self.options.release_egg_only:
            self.check_versions()
        print ''
        input.prompt('Are you sure to continue? [OK]')
        self.build_mo_files()
        self.pre_build_check()
        if not self.options.release_egg_only:
            self.bump_version_before_tagging()
            self.create_tag()
        if self.options.release_egg:
            self.release_egg()
        if not self.options.release_egg_only:
            self.bump_version_after_tagging()

    def pre_build_check(self):
        """ Check if a build will work later. Check this before doing anything
        by building and loading the egg.
        """
        output.part_title('Make a test-build for preventing bad dists')
        cwd = os.getcwd()
        # make a sdist
        runcmd('%s setup.py sdist' % sys.executable)
        os.chdir('dist')
        # switch dir
        print output.colorize('cd dist', output.INFO)
        # extract
        runcmd('tar -xf *.tar.gz')
        # find extracted dir / chdir
        distdir = None
        for file_ in os.listdir('.'):
            if os.path.isdir(file_):
                distdir = file_
                break
        if not distdir:
            output.error('Something is wrong: could not find extracted dist directory',
                         exit=1)
        os.chdir(distdir)
        print output.colorize('cd %s' % distdir, output.INFO)
        # test setup.py
        cmd = '%s setup.py egg_info' % sys.executable
        state, response, error = runcmd_with_exitcode(cmd,
                                                      respond=True,
                                                      respond_error=True)
        # cd back to original dir
        os.chdir(cwd)
        # remove stuff
        runcmd('rm -rf dist')
        # did it work?
        if state != 0:
            output.error('Something\'s wrong: could not load setup.py on distribution, ' +\
                             'you may have a problem with your setup.py / MANIFEST.in:',
                         exit=(not error and True or False))
            if response:
                print output.colorize(response, output.INFO)
            if error:
                output.error(error, exit=True)

        # check locales
        locales_dir = os.path.join(scm.get_package_name('.').replace('.', '/'),
                                   'locales')
        if os.path.isdir(locales_dir):
            for basedir, dirs, files in os.walk(locales_dir):
                for file_ in files:
                    path = os.path.join(basedir, file_)
                    if path.endswith('.po'):
                        # check with msgfmt
                        exitcode, errors = runcmd_with_exitcode(
                            'msgfmt -o /dev/null %s' % path,
                            log=True,
                            respond_error=True)
                        if exitcode > 0:
                            output.error(errors, exit=True)

                        data = open(path).read()
                        if 'fuzzy' in data:
                            print path
                            output.error('You have "Fuzzy" entries in your '
                            'translations! I\'m not releasing '
                                         'it like this.', exit=True)



    def analyse(self):
        output.part_title('Checking subversion project')
        if not scm.is_scm('.'):
            # without subversion or gitsvn it doesnt work...
            output.error('Current directory is not a repository of type svn, '
            'git-svn, git.',
                         exit=True)
        # update newest remote changes
        if scm.is_git('.') or scm.is_git_svn('.'):
            git.pull_changes('.')
            git.push_committed_changes('.')
        elif scm.is_subversion('.'):
            svn.update('.')
        # remote should be there
        if scm.is_git('.') and not scm.is_git_svn('.'):
            if not git.has_remote('origin'):
                output.error('There is no remote "origin", which is needd',
                exit=True)
        # run it at repo root
        if scm.is_subversion('.') or scm.is_git_svn('.'):
            root_svn = scm.get_package_root_url('.')
            if not svn.check_project_layout(root_svn, raise_exception=False,
            ask_for_creation=False):
                # we should have the folders trunk, tags, branches in the project
                output.error('Project does not have default layout with trunk, ' +\
                                 'tags and branches. At least one folder is missing.',
                             exit=True)
            if not self.options.release_egg_only:
                here_url = scm.get_svn_url('.')
                here_root = scm.get_package_root_url('.')
                is_trunk = here_url == here_root +'/trunk'
                is_branch = '/'.join(here_url.split('/')[:-1]) == here_root + '/branches'
                if not is_trunk and not is_branch:
                    # command must be run at the "trunk" folder of a package
                    output.error('Please run this command at the root of the package ' +\
                                     '(trunk/branch folder)', exit=True)
        elif scm.is_git('.'):
            if not os.path.exists('.git'):
                output.error('Please run this command at the root of the package ' +\
                                 'checkout', exit=True)
        # .. other checks
        if not os.path.isfile('setup.py'):
            # setup.py is required
            output.error('Could not find the file ./setup.py', exit=True)
        if not os.path.isfile('docs/HISTORY.txt'):
            # docs/HISTORY.txt is required
            output.error('Could not find the file ./docs/HISTORY.txt', exit=True)
        if os.path.isfile('setup.cfg'):
            # setup.cfg is not necessary, it should not be used since the development
            # stuff makes bad distribution versions
            output.error('setup.cfg should not be used anymore')
            if input.prompt_bool('Should I delete setup.cfg?'):
                scm.remove_files('setup.cfg')
                scm.commit_files('Removed setup.cfg', 'setup.cfg')
        version_file = os.path.join(scm.get_package_name('.').replace('.', '/'),
                                    'version.txt')
        if not os.path.isfile(version_file):
            # version.txt is required
            output.error('Could not find the file %s' % version_file, exit=True)
        # check MANIFEST.in
        self.check_manifest()
        # check subversion state
        if scm.has_local_changes('.'):
            output.error('You have local changes, please commit them first.',
                         exit=True)

    def check_doc(self):
        if self.options.ignore_doc_errors:
            return
        output.part_title('Checking setup.py docstring (restructuredtext)')
        cmd = '%s setup.py check --restructuredtext --strict' % sys.executable
        if runcmd_with_exitcode(cmd, log=0)!=0:
            output.error('You have errors in your docstring (README.txt, HISTORY.txt, ...)'+\
                             '\nRun "ftw checkdocs" for more details.', exit=1)

    def check_versions(self):
        output.part_title('Checking package versions')
        version_file = os.path.join(scm.get_package_name('.').replace('.', '/'),
                                    'version.txt')
        trunk_version = open(version_file).read().strip()
        print ' * Current version of trunk:         %s' %\
            output.colorize(trunk_version, output.WARNING)
        next_version = trunk_version.split('-')[0]
        existing_tags = scm.get_existing_tags('.')
        if next_version in existing_tags.keys():
            output.warning('Tag %s already existing' % next_version)
        # ask for next tag version
        prompt_msg = 'Which version do you want to release now? [%s]' % \
            output.colorize(next_version, output.BOLD_WARNING)
        next_version_input = input.prompt(prompt_msg, lambda v:v in existing_tags.keys() and 'Tag already existing' or True)
        if next_version_input:
            next_version = next_version_input
        # ask for next trunk version
        next_trunk_version = next_version + '-dev'
        next_trunk_version = self.bump_version_proposal(next_trunk_version)
        prompt_msg = 'Which version should trunk have afterwards? [%s]' % \
            output.colorize(next_trunk_version, output.BOLD_WARNING)
        next_trunk_version_input = input.prompt(prompt_msg)
        if next_trunk_version_input:
            next_trunk_version = next_trunk_version_input
        print ' * The version of the tag will be:   %s' %\
            output.colorize(next_version, output.WARNING)
        print ' * New version of the trunk will be: %s' %\
            output.colorize(next_trunk_version, output.WARNING)
        self.new_tag_version = next_version
        self.new_trunk_version = next_trunk_version

    def bump_version_proposal(self, version):
        try:
            version_parts = version.split('-')
            version = version_parts[0].split('.')
            last_num = version[-1]
            # increase
            try:
                last_num = str( int( last_num ) + 1 )
            except ValueError:
                last_num_pos = last_num[-1]
                last_num_pos = str( int( last_num_pos ) + 1 )
                last_num = last_num[:-1] + last_num_pos
            # .. use
            version[-1] = last_num
            version_parts[0] = '.'.join(version)
            return '-'.join(version_parts)
        except ValueError:
            return '-- no proposal --'

    def check_pyprc(self):
        output.part_title('Checking .pypirc for egg-release targets')
        pypirc_path = os.path.expanduser('~/.pypirc')
        if not os.path.isfile(pypirc_path):
            # ~/.pypirc required
            output.error('Could not find the file %s' % pypirc_path, exit=True)
        config = ConfigParser.ConfigParser()
        config.readfp(open(pypirc_path))
        indexservers = config.get('distutils', 'index-servers').strip().split('\n')
        sections = []
        basic_namespace = scm.get_package_name('.').split('.')[0]
        for srv in indexservers:
            # test if its properly configured
            if config.has_section(srv):
                print '* found target "%s"' % output.colorize(srv,
                                                              output.WARNING)
                sections.append(srv)
        if basic_namespace in sections:
            self.pypi_target = basic_namespace
        else:
            self.pypi_target = ''
        msg = 'Please specify a pypi target for the egg relase [%s]' % \
            output.colorize(self.pypi_target, output.BOLD_WARNING)
        pypi_target_input = input.prompt(msg, lambda v:\
                                             (self.pypi_target and not v) or v in
                                         sections
                                         and True or 'Please select a target listed above')
        if pypi_target_input:
            self.pypi_target = pypi_target_input

    def bump_version_before_tagging(self):
        """Sets the version in version.txt and HISTORY.txt from the
        trunk version (e.g. 1.0-dev) to the tag-version (1.0).

        """
        output.part_title('Bumping versions')
        version_file = os.path.join(scm.get_package_name('.').replace('.', '/'),
                                    'version.txt')
        print '* updating %s: set version to %s' % (version_file,
                                                    self.new_tag_version)
        version_txt = open(version_file, 'w')
        version_txt.write(self.new_tag_version)
        version_txt.close()
        # commit
        msg = 'bumping version to %s' % self.new_tag_version
        scm.commit_files(msg, version_file)

    def build_mo_files(self):
        """Build mo files in locales and i18n dirs
        """
        output.part_title('Build .mo files')
        po_files_to_build = []

        for basedir, dirs, files in os.walk(os.path.abspath('.')):
            if basedir.endswith('i18n') or basedir.endswith('LC_MESSAGES'):
                for file_ in files:
                    if file_.endswith('.po'):
                        po_files_to_build.append(os.path.join(basedir, file_))

        for path in po_files_to_build:
            runcmd('msgfmt %s -o %s' % (path, path[:-3] + '.mo'),
                   log=True)



    def create_tag(self):
        output.part_title('Creating subversion tag')
        if scm.is_subversion('.'):
            root_url = scm.get_package_root_url('.')
            trunk_url = scm.get_svn_url('.')
            tag_url = os.path.join(root_url, 'tags', self.new_tag_version)
            cmd = 'svn cp %s %s -m "creating tag %s for package %s"' % (
                trunk_url,
                tag_url,
                self.new_tag_version,
                svn.get_package_name('.'),
                )
            runcmd(cmd)
        elif scm.is_git_svn('.'):
            cmd = 'git svn tag %s' % self.new_tag_version
            runcmd(cmd)
            git.pull_changes('.')
        elif scm.is_git('.'):
            runcmd('git tag -a %s -m "tagged by ftw.manager"' % self.new_tag_version, log=True)
            runcmd('git push origin --tags', log=True)

    def bump_version_after_tagging(self):
        """Bump the version in the trunk / branch / master after
        creating the tag. Update version.txt and HISTORY.txt

        """
        output.part_title('Bumping versions in trunk')
        version_file = os.path.join(scm.get_package_name('.').replace('.', '/'),
                                    'version.txt')
        print '* updating %s: set version to %s' % (version_file,
                                                    self.new_trunk_version)
        version_txt = open(version_file, 'w')
        version_txt.write(self.new_trunk_version)
        version_txt.close()
        history_file = 'docs/HISTORY.txt'
        print '* updating %s' % history_file
        insert_title_on_line = 3
        version = self.new_trunk_version.split('-')[0]
        data = open(history_file).read().split('\n')
        data = data[:insert_title_on_line] +\
            ['', version,'-' * len(version), '', ] +\
            data[insert_title_on_line:]
        file = open(history_file, 'w')
        file.write('\n'.join(data))
        file.close()
        # commit
        ci_msg = 'bumping versions in trunk of %s after tagging %s' % (
            scm.get_package_name('.'),
            self.new_tag_version,
            )
        scm.commit_files(ci_msg, '*', push=True)

    def release_egg(self):
        output.part_title('Releasing agg to target %s' % self.pypi_target)
        sdist_params = ''
        
        # Workaround for broken tarfile implementation in python 2.4
        # more infos at http://bugs.python.org/issue4218
        # Only python 2.4.x is affected
        if  (2, 5) > sys.version_info > (2, 4): 
            # Probably sys.hexinfo would be the better solution
            output.part_title(
                'Python 2.4.x detected, use sdist with --formats=zip')
            sdist_params = '--formats=zip'

        cmd = '%s setup.py mregister sdist %s mupload -r %s' % (
            sys.executable,
            sdist_params,
            self.pypi_target
            )
        runcmd(cmd)
        runcmd('rm -rf dist build')


    def check_manifest(self):
        """ Checks the MANIFEST.in file and gives advices. It returns if the
        release action can be continued
        """
        if self.options.release_egg_only:
            return True

        namespace = scm.get_package_name('.').split('.')[0]

        required_lines = (
            'recursive-include %s *' % namespace,
            'recursive-include docs *',
            'include *.txt',
            'global-exclude *.pyc',
            'global-exclude ._*',
            )

        unused_lines = (
            'include setup.py',
            'include README.txt',
            'include CONTRIBUTORS.txt',
            'global-exclude *pyc',
            'global-exclude *mo',
            'global-exclude *.mo',
            )

        created = False
        modified = False
        commit_message = ''

        if not os.path.isfile('MANIFEST.in'):
            output.warning('Could not find the file ./MANIFEST.in, creating one')
            f = open('MANIFEST.in', 'w')
            f.write('\n'.join(required_lines))
            f.close()
            print 'created MANIFEST.in with following content:'
            print output.colorize(open('MANIFEST.in').read(), output.INFO)
            print ''
            commit_message = 'added MANIFEST.in for %s' % scm.get_package_name('.')
            created = True

        else:
            # check the existing file
            current_lines = [x.strip() for x in open('MANIFEST.in').readlines()]
            missing_lines = [x for x in required_lines
                             if x.strip() not in current_lines]
            files_to_remove = [x for x in unused_lines
                               if x.strip() in current_lines]

            if len(missing_lines) > 0 or len(files_to_remove) > 0:
                new_lines = current_lines

                if len(missing_lines) > 0:
                    output.warning('./MANIFEST.in: added some required lines:')
                    print output.colorize('\n'.join(missing_lines), output.INFO)
                    print ''
                    new_lines += missing_lines

                if len(files_to_remove) > 0:
                    output.warning('./MANIFEST.in: removed some unused lines:')
                    print output.colorize('\n'.join(files_to_remove), output.ERROR)
                    print ''
                    new_lines = filter(lambda x:x.strip() not in files_to_remove,
                                       new_lines)

                f = open('MANIFEST.in', 'w')
                f.write('\n'.join(new_lines))
                f.close()
                commit_message = 'updated MANIFEST.in for %s' % scm.get_package_name('.')
                modified = True

        if created or modified:
            # commit it ?
            if input.prompt_bool('Would you like to commit the MANIFEST.in?'):
                if created:
                    scm.add_and_commit_files(commit_message, 'MANIFEST.in')
                    return True
                elif modified:
                    scm.commit_files(commit_message, 'MANIFEST.in')
                    return True
            return False

        else:
            return True

basecommand.registerCommand(ReleaseCommand)
