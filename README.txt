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

--help-text--
