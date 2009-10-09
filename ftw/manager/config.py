
import os.path
import ConfigParser

from ftw.manager.utils import singleton
from ftw.manager.utils.memoize import memoize

class Configuration(singleton.Singleton):

    @property
    @memoize
    def config(self):
        config_file = os.path.expanduser('~/.ftw.manager/config')
        config = ConfigParser.RawConfigParser()
        config.read(config_file)
        return config

    @property
    @memoize
    def syntax_enabled(self):
        default = False
        if not self.color_scheme:
            return False
        elif not self.config.has_option('output', 'syntax'):
            return default
        else:
            return self.config.getboolean('output', 'syntax')

    @property
    @memoize
    def color_scheme(self):
        default = None
        if not self.config.has_option('output', 'scheme'):
            return default
        else:
            return self.config.get('output', 'scheme')

