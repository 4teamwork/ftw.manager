from setuptools import setup, find_packages
import os
import sys

version = open('ftw/manager/version.txt').read().strip()

long_description = open("README.txt").read().decode('utf8') + u"\n" + \
    open(os.path.join("docs", "HISTORY.txt")).read().decode('utf8')

generated_description = False
try:
    from ftw.manager import ftwCommand
    from ftw.manager import commands
    commands # register commands / make flymake happy
    from ftw.manager import config
    generated_description = True
except ImportError:
    pass
if generated_description:
    # disable syntax highlighting
    config.Configuration.temporary_disable_syntax_highlighting()
    # reset sys.argv
    argv = sys.argv[:]
    sys.argv = argv[:1]
    from StringIO import StringIO
    from ftw.manager.utils import output
    output.COLORSTRINGS_ENABLED = False
    help = StringIO()
    help.write('\n')
    # get base ftw help
    cmd = ftwCommand.FTWCommand()
    cmd.parser.print_help(help)
    # get command specific help messages
    for klass in cmd.commands:
        command = klass(cmd)
        title = 'ftw %s' % klass.command_name
        if klass.command_shortcut:
            title += ' (%s)' % klass.command_shortcut
        help.write('\n')
        help.write(title)
        help.write('\n')
        help.write('=' * len(title))
        help.write('\n')
        command.parser.print_help(help)
        help.write('\n')
        help.write('\n')
    # --
    help.seek(0)
    long_description.encode('ascii')
    long_description = long_description.replace(u'--help-text--', help.read())
    sys.argv[:] = argv


extras_require = {
    'i18ndude': ('i18ndude',),
    }
extras_require['all'] = zip(*extras_require.values())

setup(name='ftw.manager',
      version=version,
      description="ftw.manager provides commands for subversion, psc and egg-handling",
      long_description=long_description,
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='release subversion psc egg',
      author='Jonas Baumann',
      author_email='mailto:j.baumann@4teamwork.ch',
      url='http://psc.4teamwork.ch/4teamwork/ftw/ftw-manager/',
      license='GPL2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ftw'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools',
        # -*- Extra requirements: -*-
        'collective.dist',
        'simplejson',
        ],
      extras_require=extras_require,
      entry_points = {
        'console_scripts' : [
            'ftw = ftw.manager.ftwCommand:main',
            ],
        },
      )
