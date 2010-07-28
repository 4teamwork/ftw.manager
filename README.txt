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
translations with i18ndude).

    $ svn co https://svn.4teamwork.ch/repos/buildout/ftw.manager/
    $ cd ftw.manager
    $ python2.6 bootstrap.py
    $ bin/buildout

After a successful buildout there is a executable `bin/ftw` and some
other useful and required commands such as i18ndude.

    $ bin/ftw

For global usage it is recommended to either extend the $PATH variable
of your shell with the path to the `bin` directory or to symlink the
`bin/ftw` file to a $PATH-directory such as `/usr/local/bin`.


Development
===========

For development you can install the `ftw.manager` package from source.
Check it out to any directory and then run `python2.6 setup.py develop`
which registers the package in the site-packages and creates a `ftw`
executable in the bin folder of the python installation (which should
be in the $PATH usually). A developers buildout is planned.


Detailed Help
=============

Use the help command for detailed help:

    $ ftw.help

--help-text--
