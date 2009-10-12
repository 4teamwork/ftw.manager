
from ftw.manager.utils import singleton
from ftw.manager.utils.memoize import memoize
from ftw.manager import config

COLOR_SCHEMES = {
    'dark' : {
        'error'           : '\033[0;31m%s\033[00m',
        'error_bold'      : '\033[1;31m%s\033[00m',
        'warning'         : '\033[0;36m%s\033[00m',
        'warning_bold'    : '\033[1;36m%s\033[00m',
        'info'            : '\033[0;32m%s\033[00m',
        'info_bold'       : '\033[1;32m%s\033[00m',
    },
    'light' : {
        'error'           : '\033[0;31m%s\033[00m',
        'error_bold'      : '\033[1;31m%s\033[00m',
        'warning'         : '\033[0;33m%s\033[00m',
        'warning_bold'    : '\033[1;33m%s\033[00m',
        'info'            : '\033[0;32m%s\033[00m',
        'info_bold'       : '\033[1;32m%s\033[00m',
     },
}

class ColorString(str):

    def __new__(cls, value, color):
        self = str.__new__(cls, color % value)
        self.value = value
        self.color = color
        return self

    def __len__(self):
        return len(self.value)

    def ljust(self, width):
        s = str(self)
        if width - len(self) > 0:
            s += ' ' * (width - len(self))
        return s


class ColorScheme(singleton.Singleton):

#    @memoize
#    def __call__(self):
#        config.Configuration().
    @property
    @memoize
    def syntax_enabled(self):
        return config.Configuration().syntax_enabled

    @property
    @memoize
    def scheme(self):
        return config.Configuration().color_scheme

    @memoize
    def color(self, type):
        return COLOR_SCHEMES[self.scheme][type]


    def colorize(self, text, type):
        if not self.syntax_enabled:
            return text
        else:
            color = self.color(type)
            return ColorString(text, color)

    def color_test(self):
        import sys
        print 'COLOR TEST using color scheme:', self.scheme
        print self.colorize('This is a error text', 'error')
        print self.colorize('This is a error_bold text', 'error_bold')
        print self.colorize('This is a warning text', 'warning')
        print self.colorize('This is a warning_bold text', 'warning_bold')
        print self.colorize('This is a info text', 'info')
        print self.colorize('This is a info_bold text', 'info_bold')
        sys.exit(0)

#ColorScheme().color_test()


