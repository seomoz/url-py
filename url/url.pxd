################################################################################
# Cython declarations
################################################################################

from libcpp.string cimport string
from libcpp.unordered_set cimport unordered_set
from libcpp cimport bool


cdef extern from "url-cpp/include/psl.h" namespace "Url":
    cpdef cppclass PSL:
        PSL()
        PSL(const PSL& other)
        PSL& operator=(const PSL& other)
        @staticmethod
        PSL fromPath(const string& path)
        @staticmethod
        PSL fromString(const string& path)
        string getTLD(const string& host) except +
        string getPLD(const string& host) except +


cdef extern from "url-cpp/include/url.h" namespace "Url":
    cpdef cppclass Url:
        Url(const string& url) except +ValueError
        Url& assign(const Url& other)
        bool equiv(const Url& other)
        bool operator==(const Url& other)

        # Getters
        const string& scheme() const
        const string& host() const
        const int port() const
        const string& path() const
        const string& params() const
        const string& query() const
        const string& fragment() const
        const string& userinfo() const

        # Setters
        Url& setScheme(const string& s)
        Url& setHost(const string& s)
        Url& setPort(int i)
        Url& setPath(const string& s)
        Url& setParams(const string& s)
        Url& setQuery(const string& s)
        Url& setFragment(const string& s)
        Url& setUserinfo(const string& s)

        # toString
        string str() const

        # Chainable methods
        Url& strip()
        Url& abspath()
        Url& relative_to(const string& other)
        Url& relative_to(const Url& other)
        Url& escape(bool strict)
        Url& unescape()
        Url& deparam(const unordered_set[string]& blacklist)
        Url& sort_query()
        Url& remove_default_port()
        Url& deuserinfo()
        Url& defrag()
        Url& punycode() except +ValueError
        Url& unpunycode() except +ValueError
