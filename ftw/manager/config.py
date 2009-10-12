
import os.path
import ConfigParser
from StringIO import StringIO

from ftw.manager.utils import singleton
from ftw.manager.utils.memoize import memoize

DEFAULT_CONFIGURATION = '''
[output]
syntax = false
scheme = light
'''

class Configuration(singleton.Singleton):

    @property
    def config_path(self):
        return os.path.expanduser('~/.ftw.manager/config')

    @property
    @memoize
    def config(self):
        config_file = self.config_path
        config = ConfigParser.RawConfigParser()
        if os.path.exists(self.config_path):
            config.read(config_file)
        else:
            config.readfp(StringIO(DEFAULT_CONFIGURATION))
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

    def initialize_configuration(self):
        if not os.path.exists(self.config_path):
            dirname = os.path.dirname(self.config_path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            self.write_config()

    def write_config(self):
        self.config.write(open(self.config_path, 'w'))

