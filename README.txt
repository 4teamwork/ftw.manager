ftw.manager
===========

ftw.manager stellt eine Sammlung von Scripts zur Verfu ̈gung, die Entwick- lungsprozesse automatisieren sollen.

Installation
============

ftw.manager kann mit easy install installiert werden. Das Egg ist in unserem PSC eingetragen (http://psc.4teamwork.ch/4teamwork/ftw/ftw.manager).

Installation der neusten Version von ftw.manager::
    sudo easy install-2.4 -f http://downloads.4teamwork.ch/4teamwork/ftw/simple ftw.manager

Es sollte die Python-Version verwendet werden, mit welcher auch Zope läuft. Das Updaten von ftw.manager auf den neusten Release funktioniert auch mit easy install::
    sudo easy install-2.4 -U -f http://downloads.4teamwork.ch/4teamwork/ftw/simple ftw.manager

Während der Installation wird ein Script ``ftw`` im *bin*-Ordner der angegebenen Zope-Version erstellt.
Wenn dieser *bin*-Ordner noch nicht im PATH ist, dann sollte er eingetragen werden::
    ~% which python2.4
    /Library/Frameworks/Python.framework/Versions/2.4.6/bin//python2.4
    ~% echo "export PATH=/Library/Frameworks/Python.framework/Versions/2.4.6/bin:$PATH" > ~/.profile

Nach erfolgreicher Installation steht der Befehl ``ftw`` zur Verfügung::
    ~% ftw help
    usage: ftw ACTION [options]
    
    ACTIONS:
      checkdocs        : Checks if the description defined in setup.py is reStructured Text valid.
      checkout         : Checks out a package with git-svn [co]
      zopeinstance     : Run bin/instance placeless [zi]
      dependencytests  : Run tests for dependencies found in dependencies.txt [dt]
      develop          : Sets a package to develop [dev]
      help             : show help text
      i18npot          : Aktualisiert die i18n-POT-Dateien eines Packets [ib]
      i18nsync         : Aktualisiert die Übersetzungs-Dateien einer Sprache [is]
      multiinstance    : Calls multiple (ZEO-) instances one after another [mi]
      release          : Release eines Packets erstellen [rl]
      switch           : Wechselt zwischen lokalem SVN- und GIT-SVN-Repository [sw]
      test             : Run tests for current package [t]
      version          : Display Version of the package containing the current directory
    
    
    options:
      --version   show program's version number and exit
      -h, --help  show this help message and exit



