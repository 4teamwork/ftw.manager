import urllib2
from urlparse import urlparse


class HTTPRealmFinderHandler(urllib2.HTTPBasicAuthHandler):
    def http_error_401(self, req, fp, code, msg, headers):
        realm_string = headers['www-authenticate']

        q1 = realm_string.find('"')
        q2 = realm_string.find('"', q1+1)
        realm = realm_string[q1+1:q2]

        self.realm = realm


class HTTPRealmFinder:
    def __init__(self, url):
        self.url = url
        scheme, domain, path, x1, x2, x3 = urlparse(url)

        handler = HTTPRealmFinderHandler()
        handler.add_password(None, domain, 'foo', 'bar')
        self.handler = handler

        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener)

    def ping(self, url):
        try:
            urllib2.urlopen(url)
        except urllib2.HTTPError:
            pass

    def get(self):
        self.ping(self.url)
        try:
            realm = self.handler.realm
        except AttributeError:
            realm = None

        return realm

    def prt(self):
        print self.get()


def register_basic_auth_handler_for_url(url):
    """Registers a basic auth handler for the url if it seems necessary.
    """
