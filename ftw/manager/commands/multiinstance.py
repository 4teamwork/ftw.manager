from ftw.manager.commands import basecommand
from ftw.manager.utils import output
from ftw.manager.utils import runcmd
from ftw.manager.utils.memoize import memoize
import os
import time


class MultiinstanceCommand(basecommand.BaseCommand):
    u"""
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

    """

    command_name = u'multiinstance'
    command_shortcut = u'mi'
    description = u'Calls multiple (ZEO-) instances one after another'
    usage = u'ftw %s FROM [TO] ACTION' % command_name

    alias_map = {
        'adm' : 0,
    }

    def __call__(self):
        if len(self.args)<2:
            output.error('At least 2 arguments are required', exit=1)
        if len(self.args)>3:
            output.error('At most 3 arguments are required', exit=1)
        # extract and check arguments
        if len(self.args)==2:
            self.fromnr, self.action = self.args
            self.tonr = self.fromnr
        elif len(self.args)==3:
            self.fromnr, self.tonr, self.action = self.args
        self.fromnr = int(self.unalias(self.fromnr))
        self.tonr = int(self.unalias(self.tonr))
        if self.tonr < self.fromnr:
            output.error('FROM (%s) must be lower than TO (%s)' % (
                    str(self.fromnr),
                    str(self.tonr),
            ))
        # find instances
        instance_names = ['instance' + str(self.alias(x))
                            for x in range(self.fromnr, self.tonr+1)]
        instance_paths = []
        for name in instance_names:
            path = os.path.join(self.find_buildout_directory(), 'bin', name)
            if os.path.exists(path):
                instance_paths.append(path)
                print ' * found %s' % path
            else:
                output.warning('%s not found: skipping' % path)
        # call instances
        for i, path in enumerate(instance_paths):
            if i!=0 and self.options.delay:
                print ' * waiting for %s second' % str(self.options.delay)
                time.sleep(self.options.delay)
            runcmd('%s %s' % (path, self.action))

    @memoize
    def find_buildout_directory(self):
        path = ['.']
        while 1:
            dir = os.listdir('/'.join(path))
            if '/'==os.path.abspath('/'.join(path)):
                output.error('No buildout directory with existing bin/instance* found', exit=1)
                # die
            if '#instance' in '#'.join(dir):
                # we are in the bin folder
                path.append('..')
                return os.path.abspath('/'.join(path))
            if 'bin' in dir:
                bin_contents = os.listdir('/'.join(path+['bin']))
                if '#instance' in '#'.join(bin_contents):
                    # valid buildout directory reached
                    return os.path.abspath('/'.join(path))
            path.append('..')

    def unalias(self, nr):
        for aName, aNr in self.alias_map.items():
            if str(nr).lower()==str(aName).lower():
                return int(aNr)
        return int(nr)

    def alias(self, nr):
        for aName, aNr in self.alias_map.items():
            if str(nr).lower()==str(aNr).lower():
                return aName
        return nr

    def register_options(self):
        self.parser.add_option('-d', '--delay', dest='delay',
                               action='store', type='int', default=1,
                               help='Timeout between two instance calls')


basecommand.registerCommand(MultiinstanceCommand)
