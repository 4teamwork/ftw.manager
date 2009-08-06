from setuptools import setup, find_packages
import os

version = open('ftw/manager/version.txt').read().split()

setup(name='ftw.manager',
      version=version,
      description="ftw.manager provides commands for subversion, psc and egg-handling",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='release subversion psc egg',
      author='Jonas Baumann',
      author_email='j.baumann@4teamwork.ch',
      url='http://psc.4teamwork.ch/4teamwork/ftw/ftw.manager/',
      license='GPL2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ftw'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'collective.dist',
      ],
      entry_points = {
            'console_scripts' : [
                'ftw = ftw.manager.ftwCommand:main',
            ],
      },
      )
