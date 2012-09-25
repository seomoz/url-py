#! /usr/bin/env python
#
# Much of this code was written by @DavidBarts

'''This is a module for dealing with urls. In particular, sanitizing them.'''

import re
import codecs
import urllib
import urlparse

# Come codes that we'll need
IDNA = codecs.lookup('idna')
UTF8 = codecs.lookup('utf-8')
ASCII = codecs.lookup('ascii')
W1252 = codecs.lookup('windows-1252')


def parse(url, encoding='utf-8'):
    '''Parse the provided url string and return an URL object'''
    return URL.parse(url, encoding)


class URL(object):
    '''
    For more information on how and what we parse / sanitize:
        http://tools.ietf.org/html/rfc1808.html
    The more up-to-date RFC is this one:
        http://www.ietf.org/rfc/rfc3986.txt
    '''

    @classmethod
    def parse(cls, url, encoding):
        '''Parse the provided url, and return a URL instance'''
        if isinstance(url, unicode):
            parsed = urlparse.urlparse(url.encode('utf-8'))
        else:
            parsed = urlparse.urlparse(url.decode(encoding).encode('utf-8'))

        try:
            port = parsed.port
        except ValueError:
            port = None

        return cls(parsed.scheme, parsed.hostname, port,
            parsed.path, parsed.params, parsed.query, parsed.fragment)

    def __init__(self, scheme, host, port, path, params, query, fragment):
        self._scheme = scheme
        self._host = host
        self._port = port
        self._path = path or '/'
        self._params = re.sub(r'^;+', '', params)
        self._params = re.sub(r'^;|;$', '', re.sub(r';{2,}', ';', self._params))
        # Strip off extra leading ?'s
        self._query = re.sub(r'^\?+', '', query)
        self._query = re.sub(r'^&|&$', '', re.sub(r'&{2,}', '&', self._query))
        self._fragment = fragment

    def equiv(self, other):
        '''Return true if this url is equivalent to another'''
        pass

    def __eq__(self, other):
        '''Return true if this url is /exactly/ equal to another'''
        if isinstance(other, basestring):
            return self.__eq__(self.parse(other))
        return (
            self._scheme   == other._scheme and
            self._host     == other._host   and
            self._path     == other._path   and
            self._port     == other._port   and
            self._params   == other._params and
            self._query    == other._query  and
            self._fragment == other._fragment)

    def canonical(self):
        '''Canonicalize this url. This includes reordering parameters and args
        to have a consistent ordering'''
        self._query = '&'.join(sorted([q for q in self._query.split('&')]))
        self._params = ';'.join(sorted([q for q in self._params.split(';')]))
        return self

    def defrag(self):
        '''Remove the fragment from this url'''
        self._fragment = None
        return self

    def deparam(self, params=None):
        '''Strip any of the provided parameters out of the url'''
        # And remove all the black-listed query parameters
        self._query = '&'.join(q for q in self._query.split('&')
            if q.partition('=')[0].lower() not in params)
        # And remove all the black-listed param parameters
        self._params = ';'.join(q for q in self._params.split(';') if
            q.partition('=')[0].lower() not in params)
        return self

    def abspath(self):
        '''Clear out any '..' and excessive slashes from the path'''
        # Remove double forward-slashes from the path
        self._path = re.sub(r'\/{2,}', '/', self._path)
        # With that done, go through and remove all the relative references
        unsplit = []
        for part in self._path.split('/'):
            # If we encounter the parent directory, and there's
            # a segment to pop off, then we should pop it off.
            if part == '..' and (not unsplit or unsplit.pop() != None):
                pass
            elif part != '.':
                unsplit.append(part)

        # With all these pieces, assemble!
        self._path = '/'.join(unsplit)
        return self

    def lower(self):
        '''Lowercase the hostname'''
        self._host = self._host.lower()
        return self

    def sanitize(self):
        '''A shortcut to abspath, escape and lowercase'''
        return self.abspath().escape().lower()

    def escape(self):
        '''Make sure that the path is correctly escaped'''
        self._path = urllib.quote(urllib.unquote(self._path))
        return self

    def unescape(self):
        '''Unescape the path'''
        self._path = urllib.unquote(self._path)
        return self

    # Return string versions of the url
    def unicode(self):
        '''Return a unicode version of this url'''
        return self.encode('utf-8').decode('utf-8')

    def utf8(self):
        '''Return a utf-8 version of this url'''
        return self.encode('utf-8')

    def encode(self, encoding):
        '''Return the url in an arbitrary encoding'''
        netloc = self._host
        if self._port:
            netloc += (':' + self._port)

        result = urlparse.urlunparse((self._scheme, netloc, self._path,
            self._params, self._query, self._fragment))
        return result.decode('utf-8').encode(encoding)

    def relative(self, path):
        '''Evaluate the new path relative to the current url'''
        pass

    def punycode(self):
        '''Convert to punycode hostname'''
        self._host = IDNA.encode(self._host.decode('utf-8'))[0]
        return self

    def unpunycode(self):
        '''Convert to an unpunycoded hostname'''
        self._host = IDNA.decode(self._host.decode('utf-8'))[0].encode('utf-8')
        return self
