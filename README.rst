ftw.manager
===========

The `ftw.manager` provides various tools for development according
to written and unwritten 4teamwork guidelines.


Installation
============

It's recommended to install it with a prepared buildout, because the
it has various heavy dependencies which may install zope to your
site-packages when you use easy_install - which is really bad.

You can install it with the python version you prefer, but a version
of >= 2.4 is recommended. The python version you choose for bootstrapping
is used for any commands run by `ftw.manager` (such as building and
releasing packages, checking python code with pyflakes or creating
translations with i18ndude)::

    $ svn co https://svn.4teamwork.ch/repos/buildout/ftw.manager/
    $ cd ftw.manager
    $ python2.6 bootstrap.py
    $ bin/buildout

After a successful buildout there is a executable `bin/ftw` and some
other useful and required commands such as i18ndude::

    $ bin/ftw

For global usage it is recommended to either extend the $PATH variable
of your shell with the path to the `bin` directory or to symlink the
`bin/ftw` file to a $PATH-directory such as `/usr/local/bin`.

You need to install `setuptools` and `collective.dist` with easy_install
to your site-packages (they are required for `python setup.py` calls)::

    $ easy_install-2.X setuptools collective.dist


Development
===========

For development you can install the `ftw.manager` package from source.
Check it out to any directory and then run `python2.6 setup.py develop`
which registers the package in the site-packages and creates a `ftw`
executable in the bin folder of the python installation (which should
be in the $PATH usually). A developers buildout is planned.


Known Problems
==============

Invalid command 'check'
-----------------------

When running `ftw checkdocs` or `ftw release` you may get this error::

    my.egg% ftw cd
      % /opt/local/Library/Frameworks/Python.framework/Versions/2.6/Resources/Python.app/Contents/MacOS/Python setup.py check --restructuredtext --strict
    usage: setup.py [global_opts] cmd1 [cmd1_opts] [cmd2 [cmd2_opts] ...]
       or: setup.py --help [cmd1 cmd2 ...]
       or: setup.py --help-commands
       or: setup.py cmd --help
    error: invalid command 'check'

If you get this error you need to install `collective.dist` to your site-packages.
(It does not solve the problem when adding it to the ftw.manager-buildout, since
we call the setup.py with python2.X setup.py).


Problems after moving package from subversion to git
----------------------------------------------------

After moving a package from subversion to git there may be problems with ftw.manager.
The Problem is that you have a '[svn-remote ..]' part in your `.git/config` file and
the ftw.manager then thinks he can get the SVN-Url with `git svn status`, but according
to the manual from the devwiki we have to make changes which result in a corrupt svn-remote.

Error::

    ~:~/Plone/buildouts/opengever-plone4/src/opengever.journal$ ftw ib
      Unable to determine upstream SVN information from working tree history

    Traceback (most recent call last):
     File "/Users/tom/Plone/bin/ftw", line 15, in <module>
       ftw.manager.ftwCommand.main()
     File "/Users/tom/Plone/eggs/ftw.manager-1.2-py2.6.egg/ftw/manager/ftwCommand.py", line 88, in main
       FTWCommand()()
     File "/Users/tom/Plone/eggs/ftw.manager-1.2-py2.6.egg/ftw/manager/ftwCommand.py", line 44, in __call__
       command(self)()
     File "/Users/tom/Plone/eggs/ftw.manager-1.2-py2.6.egg/ftw/manager/commands/i18ndude.py", line 81, in __call__
       scm.require_package_root_cwd()
     File "/Users/tom/Plone/eggs/ftw.manager-1.2-py2.6.egg/ftw/manager/utils/scm.py", line 57, in require_package_root_cwd
       while not is_package_root(cwd):
     File "/Users/tom/Plone/eggs/ftw.manager-1.2-py2.6.egg/ftw/manager/utils/memoize.py", line 8, in _mem
       dic[key] = func(*args, **kwargs)
     File "/Users/tom/Plone/eggs/ftw.manager-1.2-py2.6.egg/ftw/manager/utils/scm.py", line 154, in is_package_root
       second_last = parts[-2]
    IndexError: list index out of range


Solution: Commit / push your current changes, remove the repository and clone it again
from your origin remote, then the svn-remote is dropped.



Detailed Help
=============

Use the help command for detailed help::

    $ ftw.help


Usage: ftw ACTION [options]

ACTIONS::

    checkdocs        : Checks if the description defined in setup.py is reStructured Text valid. [cd]
    checkout         : Checks out a package with git-svn [co]
    dependencycheck  : Check Dependencies [dc]
    eggcheck         : Check some common problems on a egg [ec]
    help             : show help text
    i18npot          : Builds the .pot files in your locales directory with i18ndude [ib]
    i18nsync         : Syncs the .pot files with the .po files of alanguage. [is]
    multiinstance    : Calls multiple (ZEO-) instances one after another [mi]
    release          : Release eines Packets erstellen [rl]
    selfupdate       : DEPRECATED Updates ftw.manager with newest version from PSC using easy_install
    setup            : Configuration Wizard for ftw.manager
    switch           : Switch between SVN and GIT-SVN [sw]
    test             : Run tests for current package [t]
    version          : Display Version of the package containing the current directory
    versioninfo      : Prints version pinning information [vi]
    zopeinstance     : Run bin/instance placeless [zi]


Options:
  --version   show program's version number and exit
  -h, --help  show this help message and exit
  -D          Debug mode (for any command)

ftw checkdocs (cd)
==================
Usage: ftw checkdocs
    Command name:     checkdocs
    Command shortcut: cd

    Checks if the description defined in setup.py is reStructured Text valid.

    This command requires docutils to be installed in the site-packes of
    your python version.

    

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -s, --show-description
                        show long-description of setup.py (with line numbers)
  -b, --show-inbrowser  Show description converted into HTML in your default browser
  -o OFFROWS, --off-rows=OFFROWS
                        show N rows before and after a bad row (only if not using -s)



ftw checkout (co)
=================
Usage: ftw checkout package_name
    Command name:     checkout
    Command shortcut: co

    Checks out a package with git-svn or svn, depending on your
    configuration (see ftw setup).

    package_name : Name of the package you want to checkout

    

Options:
  --version   show program's version number and exit
  -h, --help  show this help message and exit



ftw dependencycheck (dc)
========================
Usage: ftw dependencycheck [OPTIONS]
    Command name:     dependencycheck
    Command shortcut: dc

    The "dependencycheck" Command checks the dependencies of your package and
    displays a table of all packages you have a dependency to.
    The command checks for each package if there is a new SVN tag.

    Run the command on the root of your package checkout, where your setup.py
    is.

    Caching
    The results are cached in `~/.ftw.manager` for faster access. If you do
    not trust the caching algorithm you can force a refresh with `--refresh`.

    Generated History
    WIth the `--history` option it is possible to generate a history using
    the `HISTORY.txt` files of each package which has changes in trunk or
    tag (dependending on `--dev` option).

    

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -r, --refresh         Force refresh. Recalculates all infos
  -c BUILDOUT, --config=BUILDOUT
                        Buildout config file containing version infos
  -v, --verbose         Print executed commands
  -H, --history         Generate history file with all packages with a new version
  -d, --dev             List packages with modified trunk when using --history option
  -l LIMIT, --limit=LIMIT
                        Set depth limit (default 0)
  -q, --quiet           Do not ask anything
  -p, --pinning-proposal
                        Show a list of packages to upgrade with their newest version in version pinning format.



ftw eggcheck (ec)
=================
Usage: ftw eggcheck [OPTIONS]
    Command name:     eggcheck
    Command shortcut: ec

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

    

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -s, --check-setup     Check basic stuff in setup.py (maintainer, version, etc)
  -p, --check-paster    Check problems caused by paster
  -d, --check-description
                        Checks the long description / validates rEST
  -r, --check-requires  Check install_requires: search all python imports and zcml directives
  -z, --check-zcml      ZCML checks (locales registration, ...)



ftw help
========
Usage: ftw help command
    Command name:     help

    The ftw.manager egg provides various commands for daily work.

    

Options:
  --version   show program's version number and exit
  -h, --help  show this help message and exit



ftw i18npot (ib)
================
Usage: ftw i18npot
    Command name:     i18npot
    Command shortcut: ib

    Builds the .pot files in your `locales` directory. By
    default the name of your package is used as i18n domain.
    The locales diretory is expected to be in the root of your
    package (e.g. src/my.package/my/package/locales).

    The .pot files are built with `i18ndude`, which have to be
    installed (ftw.manager as a extras_require). i18ndude will
    search all msgid from the templates and where you use the
    zope message factory.

    

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -d DOMAIN, --domain=DOMAIN
                        i18n domain. Default: package name



ftw i18nsync (is)
=================
Usage: ftw i18nsync [LANG-CODE]
    Command name:     i18nsync
    Command shortcut: is

    Syncs the .pot files with the .po files of the selected
    language. The files are synced with `i18ndude`, which may
    be installed using the extras_require.

    

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -d DOMAIN, --domain=DOMAIN
                        i18n domain. Default: package name



ftw multiinstance (mi)
======================
Usage: ftw multiinstance FROM [TO] ACTION
    Command name:     multiinstance
    Command shortcut: mi

    Calls multiple (ZEO-) instances one after another with
    a given parameter.

    The Instances should be numbered.
    Example::

        bin/zeoserver
        bin/instanceadm
        bin/instance1
        bin/instance2
        bin/instance3

    instanceadm is the same as instance0

    FROM:   Number of first instance to call
    TO:     Number of last instance to call
    ACTION: The action is passed to the instance (e.g. start, stop, restart, fg)

    Examples:

    ftw multiinstance 2 3 stop
        Stops instance2 and instance3

    ftw mi 0 2 start
        Starts instanceadm, instance1 and instance2

    ftw mi --delay 50 1 2 restart
        Restarts instance1 then pauses for 50 seconds and then restarts instance2

    

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -d DELAY, --delay=DELAY
                        Timeout between two instance calls



ftw release (rl)
================
Usage: ftw release [OPTIONS]
    Command name:     release
    Command shortcut: rl

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

    

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -e, --only-egg        Do not commit changes (no tag, no versions changed), just create / submit the source
                        distribution.
  -E, --no-egg          Do not create / submit the dist, but create a tag and change the bump versions.
  -i, --ignore-doc-errors
                        Do not check if the description is valid restructured text.



ftw selfupdate
==============
Usage: ftw selfupdate [options]
    Command name:     selfupdate

    --- DEPRECATED ----
    Updates ftw.manager to the newest version from PSC using easy_install
    Uses PSC-URL: http://downloads.4teamwork.ch/4teamwork/ftw/simple

    

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -f FINDLINKS, --find-links=FINDLINKS
                        additional URL(s) to search for packages
  --ignore-warning      Ignore the warning not to use site-package insetallation.



ftw setup
=========
Usage: ftw setup
    Command name:     setup

    Setup the ftw.manager command.
    Creates a config file in $HOME/.ftw.manager/config

    

Options:
  --version   show program's version number and exit
  -h, --help  show this help message and exit



ftw switch (sw)
===============
Usage: ftw switch
    Command name:     switch
    Command shortcut: sw

    Converts the local svn checkout into a git-svn checkout and vice versa.
    The git-svn repository is initally heavy to clone, thats why it is cached
    in `~/.gitsvn` after the first clone.

    

Options:
  --version   show program's version number and exit
  -h, --help  show this help message and exit



ftw test (t)
============
Usage: ftw test
    Command name:     test
    Command shortcut: t

    Runs the tests for the current package.
    This command only works if you are in a checkout directory of
    your package and the this directory is part of a buildout.

    

Options:
  --version   show program's version number and exit
  -h, --help  show this help message and exit



ftw version
===========
Usage: ftw version
    Command name:     version

    Displays the version of the package you are currently in.

    

Options:
  --version   show program's version number and exit
  -h, --help  show this help message and exit



ftw versioninfo (vi)
====================
Usage: ftw versioninfo [-n] [-c <buildout.cfg>] [-d] [<package1> [<package2> [...]]]
    Command name:     versioninfo
    Command shortcut: vi

    This command searches all version pinnings for a specific package in
    the buildout configuration. It walks up the `extends`-list and follows
    remote KGS systems.

    The buildout config file to use can be specificed the option `-c <FILE.cfg>`,
    if the option is not used it defaults to buildout.cfg in the current working
    directory.

    The option `-n` tries to find new releases of this egg.

    Its possible to use this command for multiple packages by calling the command
    with each package as a parameter, but its also possible to use the command on
    a list of dependencies which are defined in ./setup.py

    

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -n, --new             Searches for newer versions
  -d, --dependencies    Run with dependency packages in ./setup.py
  -c BUILDOUT, --config=BUILDOUT
                        Buildout config file containing version infos



ftw zopeinstance (zi)
=====================
Usage: ftw zopeinstance action [options]
    Command name:     zopeinstance
    Command shortcut: zi

    Run bin/instance from any directory within the buildout.
    This may be useful called from a editor (e.g. vim).

    Example:
    % ftw zi fg

    

Options:
  --version   show program's version number and exit
  -h, --help  show this help message and exit




Changelog
=========


1.2.9
-----

* Dependencycheck: do not mark packages as changed if only .mo-files
  changed (since they are rebuilt in tag).
  [jbaumann]

* Added Workaround for broken tarfile implementation of python 2.4,
  use sdist --formats=zip
  [06.04.2011, mathias.leimgruber]


1.2.8
-----

* `release`: Include .mo-files in every release. The .po-files are checked
  for validitiy and should not contain fuzzy entries. The .mo-files are
  built with msgfmt when releasing.
  [jbaumann]

* `release`: Use annotated tags for git
  [jbaumann]


1.2.7
-----

* Release: Added check which refuses to release eggs containing fuzzy .po-files
  [jbaumann]


1.2.6
-----

* Release: glboally excluding ._* files, which fixes the ._*.po files problem.
  [jbaumann]


1.2.5
-----

* Updated packages with plone-4 packages according to good-py
  [13.09.2010, jbaumann]

* Added script for generating RAEDME.rst for github
  [05.08.2010, jbaumann]

* `eggcheck`: Improved various stuff, refactored package listings
  [05.08.2010, jbaumann]

* `eggcheck`: Fixed recursion problem when guessing svn urls.
  [05.08.2010, jbaumann]


1.2.4
-----

* Fixed encoding problems - again
  [03.08.2010, jbaumann]


1.2.3
-----

* Added better error message when using a erroneous svn remote with git
  [03.08.2010, jbaumann]

* `release` has now support for subversion, git-svn and git
  [03.08.2010, jbaumann]

* Translated german stuff to english, removed various
  python2.4 vs python2.6 encode / decode issues.
  [02.08.2010, jbaumann]


1.2.2
-----

* Some more encoding problems..
  [29.07.2010, jbaumann]


1.2.1
-----

* Fixed various encoding issues when accesing help with python2.6
  [29.07.2010, jbaumann]


1.2
---

* Updated README.txt with new buildout informations.
  [28.07.2010, jbaumann]

* Made `selfupdate` deprecated, since the buildout should be used.
  [28.07.2010, jbaumann]

* Removed command `dependencytests` since it requires a dependencies.txt, which
  no egg any more has and tests with "bin/instance tests" which is not the way
  to it should be done.
  [28.07.2010, jbaumann]

* Removed command `develop` since we have no longer any development setups
  requiring this command. The command did only work for policy packages with
  a dependencies.txt.
  [28.07.2010, jbaumann]

* GIT: improved non-svn-git support added regular git support to i18ndude commands
  [28.07.2010, jbaumann]

* GIT: added warnings for commands which do not support git ; cleaned up some code
  [28.07.2010, jbaumann]

* `eggcheck`: Implemented first version according to
  Issue #27 ftw.manager: Neuer Befehl zum Pruefen eines eggs
  https://extranet.4teamwork.ch/intranet/10-interne-projekte/tracker-softwareentwicklung/27
  [21.07.2010, jbaumann]

* `depenedencycheck`: Added proper support for `--limit` when generating history
  [21.07.2010, jbaumann]

* `versioninfo`: fix bug when using find-links for eggs in pypi (and -n)
  [20.07.2010, jbaumann]

* Issue #28 ftw.manager: Anzeige des Maintainers in Dependencycheck
  https://extranet.4teamwork.ch/intranet/10-interne-projekte/tracker-softwareentwicklung/28/
  `dependencycheck`: Show maintainer in dependency table
  [19.07.2010, jbaumann]

* `versioninfo`: added support for other index_urls than pypi (PSC) and added some colours
  [02.07.2010, jbaumann]


1.1.2
-----

* Issue #24 ftw.manager: Bessere .pypirc plausibilisierung beim releasen
  https://extranet.4teamwork.ch/intranet/10-interne-projekte/tracker-softwareentwicklung/24/
  [30.06.2010, jbaumann]

* `depenedncycheck`: added new option `--pinning-proposal`
  [29.06.2010, jbaumann]

* `dependencycheck`: added some more colors
  [28.06.2010, jbaumann]


1.1.1
-----

* Issue #23 ftw.manager release: MANIFEST.in besser pruefen
  https://extranet.4teamwork.ch/intranet/10-interne-projekte/tracker-softwareentwicklung/23
  [24.06.2010, jbaumann]


1.1
---

* Made dependency resolution more robust
  [22.06.2010, jbaumann]

* `dependencycheck`: performance optimisation: use always the same svn command for that
  it will be cached be @memoize
  [22.06.2010, jbaumann]

* `dependencycheck`: respect extras_require
  quit when setup.py of a dependency is not working
  [22.06.2010, jbaumann]

* Fixed bug in `dependencycheck` command
  [21.06.2010, jbaumann]

* Release command: when using git commit the trunk after all
  [18.06.2010, jbaumann]

* Issue #21 ftw.publisher: probleme mit MANIFEST.in
  https://extranet.4teamwork.ch/intranet/10-interne-projekte/tracker-softwareentwicklung/21/
  [18.06.2010, jbaumann]

* Dependencycheck: eliminated overhead when check dependencies recursively
  [18.06.2010, jbaumann]

* Release command: added --quiet option
  [18.06.2010, jbaumann]

* Issue #13 ftw.manager: Befehl zum analysieren der dependencies
  https://extranet.4teamwork.ch/intranet/10-interne-projekte/tracker-softwareentwicklung/13
  Added new command `versioninfo`
  [09.06.2010, jbaumann]

* Moved dependency of `i18ndude` to a extras_require ("i18ndude") and
  added extras_require "all"
  [09.06.2010, jbaumann]

* Release command: added some more stuff to default MANIFEST.in
  [04.06.2010, jbaumann]

* Release command: removed bdist_egg command
  [19.05.2010, jbaumann]

* Dependencycheck: added -l option for specifying depth limit
  [09.05.2010, jbaumann]

* Added debug mode (-D) which starts pdb post-mortem
  [09.05.2010, jbaumann]

* Release: Fixed bug in branch-release
  [06.05.2010, jbaumann]


1.0.11
------

* Release: Added support for releasing from a branch
  [04.05.2010, jbaumann]

* Dependencycheck: list also the package itself
  [20.04.2010, jbaumann]


1.0.10
------

* Dependencycheck: do not list the same egg multiple times
  [12.04.2010, jbaumann]

* Added --show-in-browser option for checkdocs command
  [12.04.2010, jbaumann]

* Added package name to error message "invalid project layout"
  [29.03.2010, jbaumann]

* Fixed URL in setup.py
  [22.03.2010, jbaumann]


1.0.9
-----

* Checkout command: added support for subversion
  [22.03.2010, jbaumann]

* Config: Added new config option "default VCS"
  [22.03.2010, jbaumann]


1.0.8
-----

* Release command: added support for git-svn
  [19.03.2010, jbaumann]

* Release command bug fixed: after modifying setup.cfg in tag there were no
  more carriage returns
  [19.03.2010, jbaumann]


1.0.7
-----

* Added i18ndude as dependency. Its not necessary any more to add it to buildout.
  [18.03.2010, jbaumann]


1.0.6
-----

* Removed bad characters from auto generated docu
  [18.03.2010, jbaumann]

* Help: Sort commands
  [18.03.2010, jbaumann]


1.0.5
-----

* dependency-check action: fixed bug in download cache for buildout configs
  [17.03.2010, jbaumann]


1.0.4
-----

* dependency-check action: added support for http-extends
  [16.03.2010, jbaumann]

* dependency-check action: improved history cleanup
  [24.02.2010, jbaumann]


1.0.3
-----

* dependency-check action: added --dev option, which also lists packages with trunk-changes
  [21.02.2010, jbaumann]

* dependency-check action: added --history option which generates a history containing all
  changes of upgraded packages
  [21.02.2010, jbaumann]


1.0.2
-----

* i18ndude: added support for domains other than the package name
  [04.02.2010, jbaumann]


1.0.1
-----

* git-svn checkout: added support for packages without standard svn layout (e.g. a
  missing "branches" folder).
  [04.02.2010, jbaumann]

* Fixed buildout-config issues with relative paths in other directories.
  [18.01.2010, jbaumann]


1.0
---

* Next release is 1.0 :)
  [18.01.2010, jbaumann]

* Dependency-Check: ask for svn-urls, if the guessing fails
  [18.01.2010, jbaumann]


0.1.12
------

* Dependency-Check command implemented with support for packages and for src-dirs.
  [12.01.2010, jbaumann]

* Fixed bug in utils.runcmd_with_exitcode, which caused some commands to hang
  [12.01.2010, jbaumann]

* Fixed bug in utils.git.has_local_changes
  [05.01.2010, jbaumann]

* Release command: setup.cfg should not be required, since its not required in
  packages any more
  [23.12.2009, jbaumann]


0.1.11
------

* Release command: improved version proposoal (version as 2.4rc3 are now supported)
  [02.12.2009, jbaumann]

* Added more flexibility for using commands in non-package-root folders.
  [29.10.2009, jbaumann]


0.1.10
------

* Added shortcut "cd" for command "checkdocs"
  [15.10.2009, jbaumann]

* Improved "release" command: committing MANIFEST.in automatically (user is asked)
  [15.10.2009, jbaumann]

* Improved command "checkdocs": printing the bad rows of the docstring
  for faster mistake finding
  [15.10.2009, jbaumann]

* Added auto folder creation to svn-check-layout function
  [15.10.2009, jbaumann]


0.1.9
-----

* added color scheme support
* added "setup" command


0.1.8
-----

* improved url proposal for "checkout" command (included git-svn cache directory)
* fixed bug in release command: wrong syntax for MANIFEST.in


0.1.7
-----

* using svns INGORE.TXT files as .gitignore after after running "checkout" command
* implemented switch command for switching between svn and git-svn
* implemented auto generated docstring containing the help info for each command
* added git-svn support for command "version"
* added new command "selfupdate"
* fixed some restructuredtext issues in command documentations


0.1.6.1
-------

* added --merge support to "i18npot" command
  * add a your.package-manual.pot to your locales directory and it will be merged
* fixed optparse bug: --version is now working


0.1.6
-----

* made "test" command available in git-repositories
* added "i18npot" command
* added "i18nsync" command


0.1.5
-----

* added "dependencytests" command
* added --revert option for "develop" command


0.1.4
-----

* added "multiinstance" command


0.1.3
-----

* added "develop" command
* added git-svn support
* fixed bug in "release" command: using sys.executable for deploying egg is required, because of dependency collective.dicts


0.1.2
-----

* updated README.txt : added install instructions


0.1.1
-----

* fixed MANIFEST.in


0.1
---

* Implemented command structure
* Added various helper utils
* Implemented actions:
    * zopeinstance  : Run bin/instance placeless [zi]
    * help          : show help text
    * release       : Release eines Packets erstellen [rl]
    * version       : Display Version of the package containing the current directory
    * test          : Run tests for current package [t]

