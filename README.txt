Introduction
============

Installation
============

Das Paket ftw.manager kann mit folgendem Befehl installiert werden:

::

    % easy_install -f http://download.4teamwork.ch/4teamwork/ftw/simple ftw.manager

Easy_install registriert die funktion ``ftw`` in dem *bin*-Ordner der ensprechenden
Python-Version (siehe Ausgabe während der installation). Normalerweise ist dieser
Ordner in der PATH-Variabel und somit der Befehl global verfügbar.

Mit folgendem Befehl können die Actions aufgelistet werden:

::

    ~% ftw help
    Usage: ftw ACTION [options]

    ACTIONS:
      zopeinstance  : Run bin/instance placeless [zi]
      help          : show help text
      release       : Release eines Packets erstellen [rl]
      version       : Display Version of the package containing the current directory
      test          : Run tests for current package [t]


    Options:
      --version   show program's version number and exit
      -h, --help  show this help message and exit

Update
======

ftw.manager kann mit folgendem Befehl aktualisiert werden:

::

    % easy_install -U ftw.manager


