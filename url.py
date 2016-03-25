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
except ImportError:  # pragma: no cover
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

    # Via http://www.ietf.org/rfc/rfc3986.txt
    GEN_DELIMS = ":/?#[]@"
    SUB_DELIMS = "!$&'()*+,;="
    ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    DIGIT = "0123456789"
    UNRESERVED = ALPHA + DIGIT + "-._~"
    RESERVED = GEN_DELIMS + SUB_DELIMS
    PCHAR = UNRESERVED + SUB_DELIMS + ":@"
    PATH = PCHAR + "/"
    QUERY = PCHAR + "/?"
    FRAGMENT = PCHAR + "/?"
    USERINFO = UNRESERVED + SUB_DELIMS + ":"

    PERCENT_ESCAPING_RE = re.compile('(%([a-fA-F0-9]{2})|.)', re.S)

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

        userinfo = parsed.username
        if userinfo and parsed.password:
            userinfo += ':%s' % parsed.password

        return cls(parsed.scheme, parsed.hostname, port,
            parsed.path, parsed.params, parsed.query, parsed.fragment, userinfo)

    def __init__(self, scheme, host, port, path, params, query, fragment, userinfo=None):
        self.scheme = scheme
        self.host = host
        self.port = port
        self.path = path or '/'
        self.params = re.sub(r'^;+', '', str(params))
        self.params = re.sub(r'^;|;$', '', re.sub(r';{2,}', ';', self.params))
        # Strip off extra leading ?'s
        self.query = re.sub(r'^\?+', '', str(query))
        self.query = re.sub(r'^&|&$', '', re.sub(r'&{2,}', '&', self.query))
        self.fragment = fragment
        self.userinfo = userinfo

    def copy(self):
        '''Return a new instance of an identical URL.'''
        return URL(
            self.scheme,
            self.host,
            self.port,
            self.path,
            self.params,
            self.query,
            self.fragment,
            self.userinfo)

    def equiv(self, other):
        '''Return true if this url is equivalent to another'''
        if isinstance(other, basestring):
            _other = self.parse(other, 'utf-8')
        else:
            _other = self.parse(other.utf8, 'utf-8')

        _self = self.parse(self.utf8, 'utf-8')
        _self.canonical().defrag().abspath().escape().punycode()
        _other.canonical().defrag().abspath().escape().punycode()

        result = (
            _self.scheme    == _other.scheme    and
            _self.host      == _other.host      and
            _self.path      == _other.path      and
            _self.params    == _other.params    and
            _self.query     == _other.query)

        if result:
            if _self.port and not _other.port:
                # Make sure _self.port is the default for the scheme
                return _self.port == PORTS.get(_self.scheme, None)
            elif _other.port and not _self.port:
                # Make sure _other.port is the default for the scheme
                return _other.port == PORTS.get(_other.scheme, None)
            else:
                return _self.port == _other.port
        else:
            return False

    def __eq__(self, other):
        '''Return true if this url is /exactly/ equal to another'''
        if isinstance(other, basestring):
            return self.__eq__(self.parse(other, 'utf-8'))
        return (
            self.scheme    == other.scheme    and
            self.host      == other.host      and
            self.path      == other.path      and
            self.port      == other.port      and
            self.params    == other.params    and
            self.query     == other.query     and
            self.fragment  == other.fragment  and
            self.userinfo  == other.userinfo)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.utf8

    def __repr__(self):
        return '<url.URL object "%s" >' % self.utf8

    def canonical(self):
        '''Canonicalize this url. This includes reordering parameters and args
        to have a consistent ordering'''
        self.query = '&'.join(sorted([q for q in self.query.split('&')]))
        self.params = ';'.join(sorted([q for q in self.params.split(';')]))
        return self

    def defrag(self):
        '''Remove the fragment from this url'''
        self.fragment = None
        return self

    def deparam(self, params):
        '''Strip any of the provided parameters out of the url'''
        lowered = set([p.lower() for p in params])
        def function(name, _):
            return name.lower() in lowered
        return self.filter_params(function)

    def filter_params(self, function):
        '''Remove parameters if function(name, value)'''
        def keep(query):
            name, _, value = query.partition('=')
            return not function(name, value)
        self.query = '&'.join(q for q in self.query.split('&') if q and keep(q))
        self.params = ';'.join(q for q in self.params.split(';') if q and keep(q))
        return self

    def deuserinfo(self):
        '''Remove any userinfo'''
        self.userinfo = None
        return self

    def abspath(self):
        '''Clear out any '..' and excessive slashes from the path'''
        # Remove double forward-slashes from the path
        path = re.sub(r'\/{2,}', '/', self.path)
        # With that done, go through and remove all the relative references
        unsplit = []
        directory = False
        for part in path.split('/'):
            # If we encounter the parent directory, and there's
            # a segment to pop off, then we should pop it off.
            if part == '..' and (not unsplit or unsplit.pop() != None):
                directory = True
            elif part != '.':
                unsplit.append(part)
                directory = False
            else:
                directory = True

        # With all these pieces, assemble!
        if directory:
            # If the path ends with a period, then it refers to a directory,
            # not a file path
            self.path = '/'.join(unsplit) + '/'
        else:
            self.path = '/'.join(unsplit)
        return self

    def sanitize(self):
        '''A shortcut to abspath and escape'''
        return self.abspath().escape()

    def remove_default_port(self):
        '''If a port is provided an is the default, remove it.'''
        if self.port and self.scheme and (self.port == PORTS[self.scheme]):
            self.port = None
        return self

    @staticmethod
    def percent_encode(raw, safe):
        if isinstance(raw, unicode):
            raw = UTF8.encode(raw)[0]

        def replacement(match):
            string = match.group(1)
            if len(string) == 1:
                if string in safe:
                    return string
                else:
                    return '%%%02X' % ord(string)
            else:
                # Replace any escaped entities with their equivalent if needed.
                character = chr(int(match.group(2), 16))
                if (character in safe) and not (character in URL.RESERVED):
                    return character
                return string.upper()

        return URL.PERCENT_ESCAPING_RE.sub(replacement, raw)

    def escape(self, strict=False):
        '''Make sure that the path is correctly escaped'''
        if strict:
            self.path = self.percent_encode(self.path, URL.PATH)
            self.query = self.percent_encode(self.query, URL.QUERY)
            self.params = self.percent_encode(self.params, URL.QUERY)
            if self.userinfo:
                self.userinfo = self.percent_encode(self.userinfo, URL.USERINFO)
            return self
        else:
            self.path = urllib.quote(
                urllib.unquote(self.path), safe=URL.PATH)
            # Safe characters taken from:
            #    http://tools.ietf.org/html/rfc3986#page-50
            self.query = urllib.quote(urllib.unquote(self.query),
                safe=URL.QUERY)
            # The safe characters for URL parameters seemed a little more vague.
            # They are interpreted here as *pchar despite this page, since the
            # updated RFC seems to offer no replacement
            #    http://tools.ietf.org/html/rfc3986#page-54
            self.params = urllib.quote(urllib.unquote(self.params),
                safe=URL.QUERY)
            if self.userinfo:
                self.userinfo = urllib.quote(urllib.unquote(self.userinfo),
                    safe=URL.USERINFO)
            return self

    def unescape(self):
        '''Unescape the path'''
        self.path = urllib.unquote(self.path)
        return self

    def encode(self, encoding):
        '''Return the url in an arbitrary encoding'''
        netloc = self.host or ''
        if self.port:
            netloc += (':' + str(self.port))

        if self.userinfo is not None:
            netloc = '%s@%s' % (self.userinfo, netloc)

        result = urlparse.urlunparse((str(self.scheme), str(netloc),
            str(self.path), str(self.params), str(self.query),
            self.fragment))
        return result.decode('utf-8').encode(encoding)

    def relative(self, path, encoding='utf-8', errors='replace'):
        '''Evaluate the new path relative to the current url'''
        if not isinstance(path, str):
            newurl = urlparse.urljoin(self.utf8, path.encode('utf-8', errors))
        else:
            newurl = urlparse.urljoin(
                self.utf8, path.decode(encoding, errors).encode('utf-8', errors))
        return URL.parse(newurl, 'utf-8')

    def punycode(self):
        '''Convert to punycode hostname'''
        if self.host:
            self.host = IDNA.encode(self.host.decode('utf-8'))[0]
            return self
        raise TypeError('Cannot punycode a relative url (%s)' % repr(self))

    def unpunycode(self):
        '''Convert to an unpunycoded hostname'''
        if self.host:
            self.host = IDNA.decode(
                self.host.decode('utf-8'))[0].encode('utf-8')
            return self
        raise TypeError('Cannot unpunycode a relative url (%s)' % repr(self))

    ###########################################################################
    # Information about the domain
    ###########################################################################
    @property
    def hostname(self):
        '''Return the hostname of the url.'''
        return self.host or ''

    @property
    def pld(self):
        '''Return the 'pay-level domain' of the url
            (http://moz.com/blog/what-the-heck-should-we-call-domaincom)'''
        if self.host:
            return psl.get_public_suffix(self.host)
        return ''

    @property
    def tld(self):
        '''Return the top-level domain of a url'''
        if self.host:
            return '.'.join(self.pld.split('.')[1:])
        return ''

    ###########################################################################
    # Information about the type of url it is
    ###########################################################################
    @property
    def absolute(self):
        '''Return True if this is a fully-qualified URL with a hostname and
        everything'''
        return bool(self.host)

    ###########################################################################
    # Get a string representation. These methods can't be chained, as they
    # return strings
    ###########################################################################
    @property
    def unicode(self):
        '''Return a unicode version of this url'''
        return self.encode('utf-8').decode('utf-8')

    @property
    def utf8(self):
        '''Return a utf-8 version of this url'''
        return self.encode('utf-8')
