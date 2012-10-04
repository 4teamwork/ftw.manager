from ftw.manager.commands import basecommand
from ftw.manager.commands.versioninfo import VersioninfoCommand
import re


FTW_KGS_PATTERNS = [r'https?://kgs.4teamwork.ch/.*',
                    r'^versions.cfg$',
                    ]
PLONE_KGS_PATTERNS = [r'https?://dist.plone.org/release/.*?/versions.cfg',
                      r'https?://download.zope.org/zopetoolkit/index/.*?/zopeapp-versions.cfg',
                      r'https?://download.zope.org/Zope2/index/.*?/versions.cfg',
                      r'https?://download.zope.org/zopetoolkit/index/.*?/ztk-versions.cfg',
                      ]
COLUMN_WIDTHS = (30, 10, 10, 0)


class CheckPinningsCommand(basecommand.BaseCommand):
    u"""
    This command lists all Plone / Zope packages that are pinned in one of our
    KGSs included in the buildout configuration.

    The purpose is to detect where we overwrite a version pin in a Plone or
    Zope KGS.

    The buildout config file to use can be specificed the option
    `-c <FILE.cfg>`, if the option is not used it defaults to buildout.cfg in
    the current working directory.
    """

    command_name = u'checkpinnings'
    command_shortcut = u'cp'
    description = u'Checks for unwanted version pinning overrides.'
    usage = u'ftw %s [-c <buildout.cfg>]' % command_name

    def __call__(self):
        vi_cmd = VersioninfoCommand(self.maincommand)
        self.pinning_mapping = vi_cmd._get_buildout_pinning_mapping()

        # Find 4teamwork KGS URLs
        self.ftw_kgs_urls = self._get_ftw_kgs_urls()

        # Print justified column headers
        column_titles = ['package', 'theirs', 'ours', 'KGS URL']
        for i, title in enumerate(column_titles):
            print title.ljust(COLUMN_WIDTHS[i]),
        print
        print "=" * 74
        print

        # Find all Zope / Plone KGSs and check them for pinning overrides
        for kgs in self.pinning_mapping:
            url = kgs[0]
            for pattern in PLONE_KGS_PATTERNS:
                if re.match(pattern, url):
                    print url
                    print "-" * 74
                    packages = kgs[1]
                    for pkg_name, dummy, their_version in packages:
                        # If this package is in one of our KGSs -> bad
                        our_pins = self._get_our_pins(pkg_name)
                        if not our_pins == []:
                            for our_version, our_kgs_url in our_pins:
                                fields = [pkg_name,
                                          their_version,
                                          our_version,
                                          our_kgs_url]
                                for i, field in enumerate(fields):
                                    print field.ljust(COLUMN_WIDTHS[i]),
                                print

    def _get_our_pins(self, pkg_name):
        """Given a package name, return a list of (version, url) tuples that
        show where this package is pinned in our KGSs.
        """
        for kgs_url in self.ftw_kgs_urls:
            kgs_packages = [k[1] for k in self.pinning_mapping
                            if k[0] == kgs_url][0]
            kgs_package_names = [p[0] for p in kgs_packages]
            if pkg_name in kgs_package_names:
                our_version = [p[2] for p in kgs_packages
                               if p[0] == pkg_name][0]
                yield (our_version, kgs_url)

    def _get_ftw_kgs_urls(self):
        """Extract all 4teamwork KGS URLs from a pinning mapping.
        """
        urls = []
        for kgs in self.pinning_mapping:
            url = kgs[0]
            for pattern in FTW_KGS_PATTERNS:
                if re.match(pattern, url):
                    urls.append(url)
        urls = list(set(urls))
        return sorted(urls)

    def register_options(self):
        self.parser.add_option('-c', '--config', dest='buildout',
                               action='store', default='./buildout.cfg',
                               help='Buildout config file containing version'
                                    'infos')

basecommand.registerCommand(CheckPinningsCommand)
