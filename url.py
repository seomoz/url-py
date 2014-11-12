#!/usr/bin/env python
#
# Copyright (c) 2012-2013 SEOmoz, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''This is a module for dealing with urls. In particular, sanitizing them.'''

import re
import codecs
import urllib
try:
    import urlparse
except ImportError:
    # Python 3 support
    import urllib.parse as urlparse

# For publicsuffix utilities
from publicsuffix import PublicSuffixList
psl = PublicSuffixList()

# Come codes that we'll need
IDNA = codecs.lookup('idna')
UTF8 = codecs.lookup('utf-8')
ASCII = codecs.lookup('ascii')
W1252 = codecs.lookup('windows-1252')

# The default ports associated with each scheme
PORTS = {
    'http': 80,
    'https': 443
}

# Character classes, from RFC 3986. It is very bad form to %-encode anything
# in PCHAR in the path part of a URL, or in QUERY in the query part. In fact,
# it is *illegal* to encode anything in GEN_DELIMS or SUB_DELIMS which is
# also in QUERY or PCHAR. When normalizing, it is also illegal to decode any
# %XX sequences which correspond to anything in GEN_DELIMS or SUB_DELIMS.
# This is because, e.g., ',' and '%2C' are *not equivalent* in the path;
# both forms are allowed, but result in different URLs.
GEN_DELIMS = ":/?#[]@"
SUB_DELIMS = "!$&'()*+,;="
ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
DIGIT = "0123456789"
UNRESERVED = ALPHA + DIGIT + "-._~"
RESERVED = GEN_DELIMS + SUB_DELIMS
PCHAR = UNRESERVED + SUB_DELIMS + ":@/"  # Slash legal in path, so include it
QUERY = PCHAR + "?"  # Slash already included above.
USERINFO = UNRESERVED + SUB_DELIMS + ":"
HEXDIG = DIGIT + "ABCDEFabcdef"

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
        if isinstance(url, str):
            parsed = urlparse.urlparse(
                url.decode(encoding).encode('utf-8'))
        else:
            parsed = urlparse.urlparse(url.encode('utf-8'))

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
        self._params = re.sub(r'^;+', '', str(params))
        self._params = re.sub(r'^;|;$', '', re.sub(r';{2,}', ';', self._params))
        # Strip off extra leading ?'s
        self._query = re.sub(r'^\?+', '', str(query))
        self._query = re.sub(r'^&|&$', '', re.sub(r'&{2,}', '&', self._query))
        self._fragment = fragment

    def equiv(self, other):
        '''Return true if this url is equivalent to another'''
        if isinstance(other, basestring):
            _other = self.parse(other, 'utf-8')
        else:
            _other = self.parse(other.utf8(), 'utf-8')

        _self = self.parse(self.utf8(), 'utf-8')
        _self.canonical().defrag().abspath().escape().punycode()
        _other.canonical().defrag().abspath().escape().punycode()

        result = (
            _self._scheme == _other._scheme and
            _self._host   == _other._host   and
            _self._path   == _other._path   and
            _self._params == _other._params and
            _self._query  == _other._query)

        if result:
            if _self._port and not _other._port:
                # Make sure _self._port is the default for the scheme
                return _self._port == PORTS.get(_self._scheme, None)
            elif _other._port and not _self._port:
                # Make sure _other._port is the default for the scheme
                return _other._port == PORTS.get(_other._scheme, None)
            else:
                return _self._port == _other._port
        else:
            return False

    def __eq__(self, other):
        '''Return true if this url is /exactly/ equal to another'''
        if isinstance(other, basestring):
            return self.__eq__(self.parse(other, 'utf-8'))
        return (
            self._scheme   == other._scheme and
            self._host     == other._host   and
            self._path     == other._path   and
            self._port     == other._port   and
            self._params   == other._params and
            self._query    == other._query  and
            self._fragment == other._fragment)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.utf8()

    def __repr__(self):
        return '<url.URL object "%s" >' % self.utf8()

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

    def deparam(self, params):
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
        path = re.sub(r'\/{2,}', '/', self._path)
        # With that done, go through and remove all the relative references
        unsplit = []
        for part in path.split('/'):
            # If we encounter the parent directory, and there's
            # a segment to pop off, then we should pop it off.
            if part == '..' and (not unsplit or unsplit.pop() != None):
                pass
            elif part != '.':
                unsplit.append(part)

        # With all these pieces, assemble!
        if self._path.endswith('.'):
            # If the path ends with a period, then it refers to a directory,
            # not a file path
            self._path = '/'.join(unsplit) + '/'
        else:
            self._path = '/'.join(unsplit)
        return self

    def sanitize(self):
        '''A shortcut to abspath and escape'''
        return self.abspath().escape()

    # Percent-normalize the path, query, or params (depending on allowed). A
    # careful reading of RFC 3986 reveals that we cannot use
    # urllib.quote(urllib.unqoute(...)) to do this, because for any character
    # in GEN_DELIMS or SUB_DELIMS above, the %-encoded form and the bare,
    # unencoded character are *explicitly stated to result in different URLs*.
    # Alas, urllib.unquote() provides no way to request to leave a %XX
    # sequence alone.
    def _pct_normalize(self, raw, allowed):
        global UTF8, HEXDIG

        # This only works on byte strings, so coerce input if needed.
        if isinstance(raw, unicode):
            raw = UTF8.encode(raw)[0]

        ret = ''
        lraw = len(raw)
        i = 0
        while i < lraw:
            # If it's a %XX sequence, normalize it.
            if raw[i] == '%' and i + 2 < lraw and raw[i+1] in HEXDIG and raw[i+2] in HEXDIG:
                ret += self._do_pct(raw[i:i+3], allowed)
                i += 3
                continue
            # If it's an allowed character, pass it as-is
            if raw[i] in allowed:
                ret += raw[i]
            # Else it's not allowed and must be %-encoded
            else:
                ret += '%' + '%02X' % ord(raw[i])
            i += 1

        return ret

    # Normalize a %XX sequence.
    def _do_pct(self, pxx, allowed):
        global RESERVED
        ch = chr(int(pxx[1:], 16))
        if ch in allowed and ch not in RESERVED:
            # If it's allowed and not reserved, decode it
            return ch
        else:
            # Else normalize XX to uppercase
            return pxx.upper()

    def escape(self):
        '''Make sure that the username, password, and path are correctly escaped'''
        self._path = self._pct_normalize(self._path, PCHAR)
        self._query = self._pct_normalize(self._query, QUERY)
        self._params = self._pct_normalize(self._params, QUERY)
        # if self._username is not None:
        #     self._username = self._pct_normalize(self._username, USERINFO)
        # if self._password is not None:
        #     self._password = self._pct_normalize(self._password, USERINFO)
        return self

    def unescape(self):
        '''Unescape the path'''
        self._path = urllib.unquote(self._path)
        return self

    def encode(self, encoding):
        '''Return the url in an arbitrary encoding'''
        netloc = self._host
        if self._port:
            netloc += (':' + str(self._port))

        result = urlparse.urlunparse((str(self._scheme), str(netloc),
            str(self._path), str(self._params), str(self._query),
            self._fragment))
        return result.decode('utf-8').encode(encoding)

    def relative(self, path, encoding='utf-8'):
        '''Evaluate the new path relative to the current url'''
        if not isinstance(path, str):
            newurl = urlparse.urljoin(self.utf8(),
                str(path).decode(encoding).encode('utf-8'))
        else:
            newurl = urlparse.urljoin(self.utf8(), path.encode('utf-8'))
        return URL.parse(newurl, 'utf-8')

    def punycode(self):
        '''Convert to punycode hostname'''
        if self._host:
            self._host = IDNA.encode(self._host.decode('utf-8'))[0]
            return self
        raise TypeError('Cannot punycode a relative url (%s)' % repr(self))

    def unpunycode(self):
        '''Convert to an unpunycoded hostname'''
        if self._host:
            self._host = IDNA.decode(
                self._host.decode('utf-8'))[0].encode('utf-8')
            return self
        raise TypeError('Cannot unpunycode a relative url (%s)' % repr(self))

    ###########################################################################
    # Information about the domain
    ###########################################################################
    def pld(self):
        '''Return the 'pay-level domain' of the url
            (http://moz.com/blog/what-the-heck-should-we-call-domaincom)'''
        if self._host:
            return psl.get_public_suffix(self._host)
        return ''

    def tld(self):
        '''Return the top-level domain of a url'''
        if self._host:
            return '.'.join(self.pld().split('.')[1:])
        return ''

    ###########################################################################
    # Information about the type of url it is
    ###########################################################################
    def absolute(self):
        '''Return True if this is a fully-qualified URL with a hostname and
        everything'''
        return bool(self._host)

    ###########################################################################
    # Get a string representation. These methods can't be chained, as they
    # return strings
    ###########################################################################
    def unicode(self):
        '''Return a unicode version of this url'''
        return self.encode('utf-8').decode('utf-8')

    def utf8(self):
        '''Return a utf-8 version of this url'''
        return self.encode('utf-8')
