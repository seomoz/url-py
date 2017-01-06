# cython: linetrace=True
# distutils: define_macros=CYTHON_TRACE=1

from six import text_type

from cython.operator import dereference
import pkgutil

cdef PSL psl = PSL.fromString(pkgutil.get_data('url', 'psl/2016-08-16.psl'))

def ParseMethod(cls, s, encoding='utf-8'):
    if isinstance(s, bytes):
        if encoding == 'utf-8':
            return cls(s)
        else:
            return cls(s.decode(encoding).encode('utf-8'))
    else:
        return cls(s.encode('utf-8'))

def set_psl(rules):
    global psl
    psl = PSL.fromString(as_bytes(rules))

cdef as_bytes(obj):
    if isinstance(obj, text_type):
        return obj.encode('utf-8')
    return obj

cdef class StringURL:
    '''Wrapper around url-cpp, which deals in strings.'''

    cdef Url *ptr

    parse = classmethod(ParseMethod)

    def __cinit__(self, const string& s):
        self.ptr = new Url(s)

    def __dealloc__(self):
        del self.ptr

    property scheme:
        def __get__(self):
            return self.ptr.scheme()
        def __set__(self, s):
            self.ptr.setScheme(as_bytes(s))

    property host:
        def __get__(self):
            return self.ptr.host()
        def __set__(self, s):
            self.ptr.setHost(as_bytes(s))

    property port:
        def __get__(self):
            return self.ptr.port()
        def __set__(self, i):
            self.ptr.setPort(i)

    property path:
        def __get__(self):
            return self.ptr.path()
        def __set__(self, s):
            self.ptr.setPath(as_bytes(s))

    property params:
        def __get__(self):
            return self.ptr.params()
        def __set__(self, s):
            self.ptr.setParams(as_bytes(s))

    property query:
        def __get__(self):
            return self.ptr.query()
        def __set__(self, s):
            self.ptr.setQuery(as_bytes(s))

    property fragment:
        def __get__(self):
            return self.ptr.fragment()
        def __set__(self, s):
            self.ptr.setFragment(as_bytes(s))

    property userinfo:
        def __get__(self):
            return self.ptr.userinfo()
        def __set__(self, s):
            self.ptr.setUserinfo(as_bytes(s))

    def copy(self):
        '''Return a new instance of an identical URL.'''
        new = StringURL(b'')
        new.ptr.assign(dereference(self.ptr));
        return new

    def equiv(self, other, encoding='utf-8'):
        '''Return true if this url is equivalent to another'''
        if isinstance(other, basestring):
            return self.equiv(self.parse(other, encoding))
        return self.ptr.equiv(dereference((<StringURL?>other).ptr))

    def __richcmp__(self, other, op):
        '''Return true if this url is /exactly/ equal to another'''
        if op == 2:  # ==
            if isinstance(other, basestring):
                return self.__eq__(self.parse(other, 'utf-8'))
            return dereference((<StringURL>self).ptr) == dereference((<StringURL?>other).ptr)
        elif op == 3:  # !=
            return not (self == other)
        else:
            raise NotImplementedError(
                '%s does not support this operation.' % type(self).__name__)

    def __unicode__(self):
        return self.unicode

    def __str__(self):
        return self.utf8

    def __bytes__(self):
        return self.utf8

    def __repr__(self):
        return '<url.URL object "%s" >' % str(self)

    def canonical(self):
        self.ptr.sort_query()
        return self

    def defrag(self):
        '''Remove the fragment from this url'''
        self.ptr.defrag()
        return self

    def deparam(self, params):
        '''Strip any of the provided parameters out of the url'''
        lowered = unordered_set[string](as_bytes(p.lower()) for p in params)
        self.ptr.deparam(lowered)
        return self

    def filter_params(self, function):
        '''Remove parameters if function(name, value), name and value are bytes.'''
        def keep(query):
            name, _, value = query.partition('=')
            return not function(name, value)
        self.query = '&'.join(q for q in self.query.split('&') if q and keep(q))
        self.params = ';'.join(q for q in self.params.split(';') if q and keep(q))
        return self

    def deuserinfo(self):
        '''Remove any userinfo'''
        self.ptr.deuserinfo()
        return self

    def strip(self):
        '''
        Strip semantically meaningless excess '?', '&', and ';' characters from query
        and params.
        '''
        self.ptr.strip()
        return self

    def abspath(self):
        '''Clear out any '..' and excessive slashes from the path'''
        self.ptr.abspath()
        return self

    def relative(self, other):
        '''Evaluate other relative to self.'''
        if isinstance(other, basestring):
            return self.parse(other).relative_to(self)
        else:
            return other.relative_to(self)

    def relative_to(self, base):
        '''Evaluate the new path relative to the current url'''
        if isinstance(base, bytes):
            self.ptr.relative_to(<string>base)
        elif isinstance(base, unicode):
            self.ptr.relative_to(<string>(base.encode('utf-8')))
        else:
            self.ptr.relative_to(<const Url&>dereference((<StringURL?>base).ptr))
        self.ptr.abspath()
        return self

    def sanitize(self):
        '''A shortcut to abspath and escape'''
        self.ptr.abspath().escape(False)
        return self

    def remove_default_port(self):
        '''If a port is provided and is the default, remove it.'''
        self.ptr.remove_default_port()
        return self

    def escape(self, strict=False):
        '''Make sure that the path is correctly escaped'''
        self.ptr.escape(<bool>strict)
        return self

    def unescape(self):
        '''Replace entities with their corresponding byte values'''
        self.ptr.unescape()
        return self

    def encode(self, encoding):
        '''Return the url in an arbitrary encoding'''
        if encoding == 'utf-8' or encoding == 'utf8':
            return self.ptr.str()
        else:
            return self.ptr.str().decode('utf-8').encode(encoding)

    def punycode(self):
        '''Convert to punycode hostname'''
        self.ptr.punycode()
        return self

    def unpunycode(self):
        '''Convert to an unpunycoded hostname'''
        self.ptr.unpunycode()
        return self

    ###########################################################################
    # Information about the domain
    ###########################################################################
    property hostname:
        def __get__(self):
            return self.host

    property pld:
        '''Return the 'pay-level domain' of the url
            (http://moz.com/blog/what-the-heck-should-we-call-domaincom)'''
        def __get__(self):
            if not self.ptr.host().empty():
                return psl.getPLD(self.ptr.host())
            return b''

    property tld:
        '''Return the top-level domain of a url'''
        def __get__(self):
            if not self.ptr.host().empty():
                return psl.getTLD(self.ptr.host())
            return b''

    property absolute:
        '''Return True if this is a fully-qualified URL with a hostname and everything'''
        def __get__(self):
            if self.ptr.host().empty():
                return False
            return True

    property unicode:
        '''Return a unicode version of this url'''
        def __get__(self):
            return self.ptr.str().decode('utf-8')

    property utf8:
        '''Return a utf-8 version of this url'''
        def __get__(self):
            return self.ptr.str()


cdef class UnicodeURL(StringURL):
    '''A version of the URL class that deals in Unicode.'''
    property scheme:
        def __get__(self):
            return text_type(self.ptr.scheme(), encoding='utf-8')
        def __set__(self, s):
            self.ptr.setScheme(as_bytes(s))

    property host:
        def __get__(self):
            return text_type(self.ptr.host(), encoding='utf-8')
        def __set__(self, s):
            self.ptr.setHost(as_bytes(s))

    property path:
        def __get__(self):
            return text_type(self.ptr.path(), encoding='utf-8')
        def __set__(self, s):
            self.ptr.setPath(as_bytes(s))

    property params:
        def __get__(self):
            return text_type(self.ptr.params(), encoding='utf-8')
        def __set__(self, s):
            self.ptr.setParams(as_bytes(s))

    property query:
        def __get__(self):
            return text_type(self.ptr.query(), encoding='utf-8')
        def __set__(self, s):
            self.ptr.setQuery(as_bytes(s))

    property fragment:
        def __get__(self):
            return text_type(self.ptr.fragment(), encoding='utf-8')
        def __set__(self, s):
            self.ptr.setFragment(as_bytes(s))

    property userinfo:
        def __get__(self):
            return text_type(self.ptr.userinfo(), encoding='utf-8')
        def __set__(self, s):
            self.ptr.setUserinfo(as_bytes(s))

    property pld:
        '''Return the 'pay-level domain' of the url
            (http://moz.com/blog/what-the-heck-should-we-call-domaincom)'''
        def __get__(self):
            if not self.ptr.host().empty():
                return psl.getPLD(self.ptr.host()).decode('utf-8')
            return u''

    property tld:
        '''Return the top-level domain of a url'''
        def __get__(self):
            if not self.ptr.host().empty():
                return psl.getTLD(self.ptr.host()).decode('utf-8')
            return u''

    def __str__(self):
        return self.unicode
