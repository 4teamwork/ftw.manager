ftw.manager
===========

ftw.manager stellt eine Sammlung von Scripts zur Verfügung, die
Entwicklungsprozesse automatisieren sollen.

Installation
============

ftw.manager kann mit easy install installiert werden. Das Egg ist in unserem PSC
eingetragen (http://psc.4teamwork.ch/4teamwork/ftw/ftw.manager).

Installation der neusten Version von ftw.manager::

    sudo easy_install-2.4 -f http://downloads.4teamwork.ch/4teamwork/ftw/simple ftw.manager

Es sollte die Python-Version verwendet werden, mit welcher auch Zope läuft. Das
Updaten von ftw.manager auf den neusten Release funktioniert auch mit easy
install::

    sudo easy_install-2.4 -U -f http://downloads.4teamwork.ch/4teamwork/ftw/simple ftw.manager


Während der Installation wird ein Script ``ftw`` im *bin*-Ordner der angegebenen
Zope-Version erstellt. Wenn dieser *bin*-Ordner noch nicht im PATH ist, dann
sollte er eingetragen werden::

    ~% which python2.4
    /Library/Frameworks/Python.framework/Versions/2.4.6/bin//python2.4
    ~% echo "export PATH=/Library/Frameworks/Python.framework/Versions/2.4.6/bin:$PATH" >> ~/.profile

Nach erfolgreicher Installation steht der Befehl ``ftw`` zur Verfügung::
    ftw help
    --help-text--


