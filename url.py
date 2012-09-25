#! /usr/bin/env python
#
# Much of this code was written by @DavidBarts

'''This is a module for dealing with urls. In particular, sanitizing them.'''

import re
import codecs
import urllib
import string
import urlparse

# Come codes that we'll need
IDNA = codecs.lookup('idna')
UTF8 = codecs.lookup('utf-8')
ASCII = codecs.lookup('ascii')
W1252 = codecs.lookup('windows-1252')


def parse(url):
    '''Parse the provided url string and return an URL object'''
    return URL.parse(url)


class URL(object):
    '''
    For more information on how and what we parse / sanitize:
        http://tools.ietf.org/html/rfc1808.html
    The more up-to-date RFC is this one:
        http://www.ietf.org/rfc/rfc3986.txt
    '''

    @classmethod
    def parse(cls, url):
        '''Parse the provided url, and return a URL instance'''
        parsed = urlparse.urlparse(url)
        return cls(parsed.scheme, parsed.hostname, parsed.port, parsed.path,
            parsed.params, parsed.query, parsed.fragment)

    @classmethod
    def relative(cls, url, path):
        '''Evaluate the path relative to the provided url'''
        pass

    def __init__(self, scheme, host, port, path, params, query, fragment):
        self._scheme = scheme
        self._host = host
        self._port = port
        self._path = path
        self._params = params
        self._query = query
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
        self._query = re.sub(r'^&|&$', '', re.sub(r'&{2,}', '&', self._query))
        # And remove all the black-listed param parameters
        self._params = ';'.join(q for q in self._params.split(';') if
            q.partition('=')[0].lower() not in params)
        self._params = re.sub(r'^;|;$', '', re.sub(
            r';{2,}', ';', self._params))
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
        '''A shortcut to defrag, abspath and lowercase this url'''
        return self

    def escape(self):
        '''Make sure that the path is correctly escaped'''
        return self

    # Return string versions of the url
    def unicode(self):
        '''Return a unicode version of this url'''
        return u''

    def utf8(self):
        '''Return a utf-8 version of this url'''
        return ''

    def punycode(self):
        '''Return a punycode string version of this url'''
        # Most trivial case, it's an 8-bit string and it's all ASCII: just
        # return it
        if isinstance(name, str):
            wide = False
            try:
                ASCII.decode(name)
                return name
            except UnicodeDecodeError:
                try:
                    name = UTF8.decode(name)[0]
                except UnicodeDecodeError:
                    # Oink! This *shouldn't* happen, but just in case...
                    name = W1252.decode(name)[0]

        # Next-most trivial case: it's a unicode string but it's still all
        # ASCII: just return it
        elif isinstance(name, unicode):
            wide = True
            try:
                ASCII.encode(name)
                return name
            except UnicodeEncodeError:
                pass

        # This shouldn't happen
        else:
            raise TypeError('Expecting a string.')

        # It's been coerced to Unicode to make the encoder happy. Encode.
        ret = IDNA.encode(name)[0]
        return unicode(ret) if wide else ret
        return ''
