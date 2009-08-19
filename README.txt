Introduction
============

Installation
============

Das Paket ftw.manager kann mit folgendem Befehl installiert werden:

::

    % easy_install -f http://downloads.4teamwork.ch/4teamwork/ftw/simple ftw.manager

Easy_install registriert die funktion ``ftw`` in dem *bin*-Ordner der ensprechenden
Python-Version (siehe Ausgabe während der installation). Normalerweise ist dieser
Ordner in der PATH-Variabel und somit der Befehl global verfügbar.

Mit folgendem Befehl können die Actions aufgelistet werden:

::

    ~% ftw help
    usage: ftw ACTION [options]

    ACTIONS:
      checkdocs      : Checks if the description defined in setup.py is reStructured Text valid.
      checkout       : Checks out a package with git-svn [co]
      develop        : Sets a package to develop [dev]
      help           : show help text
      multiinstance  : Calls multiple (ZEO-) instances one after another [mi]
      release        : Release eines Packets erstellen [rl]
      zopeinstance   : Run bin/instance placeless [zi]
      test           : Run tests for current package [t]
      version        : Display Version of the package containing the current directory


    options:
      --version   show program's version number and exit
      -h, --help  show this help message and exit
        
Update
======

ftw.manager kann mit folgendem Befehl aktualisiert werden:

::

    % easy_install -U ftw.manager


