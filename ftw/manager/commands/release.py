# -*- coding: utf8 -*-

import basecommand
from ftw.manager.utils import output
from ftw.manager.utils import runcmd

class ReleaseCommand(basecommand.BaseCommand):
    u"""
    Der "release" command publiziert die aktuellen Änderungen eines Packets in
    einer neuen Version. Der Befehl sollte vom root-Verzeichnis eines SVN-Checkouts
    (trunk) ausgeführt werden.
    Als ausgangslage wird der Versionsname verwendet, der im setup.py eingetragen
    ist (z.B. wenn "2.0.1-dev" im setup.py steht wird eine neue Version "2.0.1"
    erstellt).

    Es werden folgende Schritte gemacht:
        * Es wird ein SVN-Tag erstellt
        * Die Version im Trunk wird erhöht (setup.py und docs/HISTORY.txt)
        * Die Version im Tag wird angepasst (setup.py und docs/HISTORY.txt)
        * Der Tag wird aufgeräumt (setup.cfg : dev-angaben entfernen)
        * Vom Tag wird ein Egg erstellt und ins pypi geladen
    """

    command_name = 'release'
    command_shortcut = 'rl'
    description = 'Release eines Packets erstellen'

    def __call__(self):
        print 'yay'

    def register_options(self):
        self.parser.add_option('-d', '--dry-run', dest='dryrun',
                               action='store_true',
                               help=u'Keine Änderungen vornehmen')


basecommand.registerCommand(ReleaseCommand)
