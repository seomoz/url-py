URL
===
URL parsing done reasonably.

[![Build Status](https://secure.travis-ci.org/seomoz/url-py.png)](http://travis-ci.org/seomoz/url-py)
![Status: Production](https://img.shields.io/badge/status-production-green.svg?style=flat)
![Team: Big Data](https://img.shields.io/badge/team-big_data-green.svg?style=flat)
![Scope: External](https://img.shields.io/badge/scope-external-green.svg?style=flat)
![Open Source: MIT](https://img.shields.io/badge/open_source-MIT-green.svg?style=flat)
![Critical: Yes](https://img.shields.io/badge/critical-yes-red.svg?style=flat)

Moz crawls. We crawl lots. In fact, you might say that crawling is our
business.

The internet's also a messy place. We've encountered some pretty crazy
implementations and servers and URLs and HTML. Over the course of this
discovery, we've found ourselves repeating certain URL sanitization tasks over
and over, so we've put them in a repo to share with the world.

At the heart of the `url` package is the `URL` object. You can get one by
passing in a unicode or string object into the top-level `parse` method. If the
string is encoded, you can provide that encoding (otherwise it's assumed to be
utf-8):

    import url

    # It knows about unicode
    myurl = url.parse(u'http://foo.com')

    # It knows about other encodings that Python supports
    myurl = url.parse(..., 'some encoding')

Internally, everything is stored as UTF-8 until you ask for a string back. The
workflow is that you'll chain a number of permutations together to get the type
of URL you're after, and then call a final method to give you a string.

    # Defrag, remove some parameters and give me a unicode string
    url.parse(...).defrag().deparam(['utm_source']).unicode()

    # Escape the path, and punycode the host, and give me a UTF-8 string
    url.parse(...).escape().punycode().utf8

    # Give me the absolute path url as some encoding
    url.parse(...).abspath().encode('some encoding')

URL Equivalence
===============
URL objects compared with `==` are interpreted very strictly, but for a more
lax interpretation, consider using `equiv` to test if two urls are functionally
equivalent:

    a = url.parse('https://föo.com:443/a/../b/.?b=2&&&&&&a=1')
    b = url.parse('https://xn--fo-fka.COM/b/?a=1&b=2')

    # These urls are not equal
    assert(a != b)
    # But they are equivalent
    assert(a.equiv(b))
    assert(b.equiv(a))

This equivalence test takes default ports for common schemes into account (so
if both urls are the same scheme, but one explicitly specifies the default
port), punycoding, case of the host name, and parameter order.

Absolute URLs
=============
You can perform many operations on relative urls (those without a hostname),
but punycoding and unpunycoding are not among them. You can also tell whether
or not a url is absolute:

    a = url.parse('foo/bar.html')
    assert(not a.absolute())

Chaining
========
Many of the methods on the `URL` class can be chained to produce a number of
effects in sequence:

    import url

    # Create a url object
    myurl = url.URL.parse('http://www.FOO.com/bar?utm_source=foo#what')
    # Remove some parameters and the fragment, spit out utf-8
    print myurl.defrag().deparam(['utm_source']).utf8

In fact, unless the function explicitly returns a string, then the method may
be chained:

`strip`
-------
Removes semantically meaningless excess '?', '&', and ';' characters from query and
params:

    >>> url.parse('http://example.com/????query=param&&&&foo=bar').strip().utf8
    'http://example.com/?query=param&foo=bar'

`canonical`
-----------
According to the RFC, the order of parameters is not supposed to matter. In
practice, it can (depending on how the server matches URL routes), but it's
also helpful to be able to put parameters in a canonical ordering. This
ordering happens to be alphabetical order:

    >>> url.parse('http://foo.com/?b=2&a=1&d=3').canonical().utf8
    'http://foo.com/?a=1&b=2&d=3'

`defrag`
--------
Remove any fragment identifier from the url. This isn't part of the reuqest
that gets sent to an HTTP server, and so it's often useful to remove the 
fragment when doing url comparisons.

    >>> url.parse('http://foo.com/#foo').defrag().utf8
    'http://foo.com/'

`deparam`
---------
Some parameters are commonly added to urls that we may not be interested in. Or
they may be misleading. Common examples include referrering pages, `utm_source`
and session ids. To strip out all such parameters from your url:

    >>> url.parse('http://foo.com/?do=1&not=2&want=3&this=4').deparam(['do', 'not', 'want']).utf8
    'http://foo.com/?this=4'

`abspath`
---------
Like its `os.path` namesake, this makes sure that the path of the url is
absolute. This includes removing redundant forward slashes, `.` and `..`.

    >>> url.parse('http://foo.com/foo/./bar/../a/b/c/../../d').abspath().utf8
    'http://foo.com/foo/a/d'

`escape`
--------
Non-ASCII characters in the path are typically encoded as UTF-8 and then
escaped as `%HH` where `H` are hexidecimal values. It's important to note that
the `escape` function is idempotent, and can be called repeatedly

    >>> url.parse(u'http://foo.com/ümlaut').escape().utf8
    'http://foo.com/%C3%BCmlaut'
    >>> url.parse(u'http://foo.com/ümlaut').escape().escape().utf8
    'http://foo.com/%C3%BCmlaut'

`unescape`
----------
If you have a URL that might have been escaped before it was given to you, but
you'd like to display something a little more meaningful than `%C3%BCmlaut`, 
you can unescape the path:

    >>> print url.parse('http://foo.com/%C3%BCmlaut').unescape().unicode()
    http://foo.com/ümlaut

`relative`
----------
Evaluate a relative path given a base url:

    >>> url.parse('http://foo.com/a/b/c').relative('../foo').utf8
    'http://foo.com/a/foo'

`punycode`
----------
For non-ASCII hostnames, they must be punycoded before a DNS request is made
for them. To this end, there's the punycode function:

    >>> url.parse('http://ümlaut.com').punycode().utf8
    'http://xn--mlaut-jva.com/'

`unpunycode`
------------
If a url may have been punycoded before it's been handed to you, and you'd like
to be able to display something nicer than `http://xn--mlaut-jva.com/`:

    >>> print url.parse('http://xn--mlaut-jva.com/').unpunycode().utf8
    http://ümlaut.com/

Other Functions
===============
Not all functions are chainable -- some return a value other than a `URL` object:

- `encode(...)` -- return a version of the url in an arbitrary encoding

Public Suffix List
==================
This library comes bundled with a version of the public suffix list. However, it may not
suit your needs (whether you need to stay pinned to an old list, or need to update to a
new list). As such, you can provide the PSL you'd like to use, as a `UTF-8` string:

```python
import url

# Read it from a file
with open('path/to/my/psl') as fin:
    url.set_psl(fin.read())

# Grab it from the PSL site
import requests
url.set_psl(requests.get('https://publicsuffix.org/list/public_suffix_list.dat').content)
```

Properties
==========
Many attributes are available on URL objects:

- `scheme` -- empty string if URL is relative
- `host` -- `None` if URL is relative
- `hostname` -- like `host`, but empty string if URL is relative
- `pld` -- the [pay-level domain](https://moz.com/blog/what-the-heck-should-we-call-domaincom),
    or an empty string if URL is relative
- `tld` -- the [top-level domain](https://en.wikipedia.org/wiki/Top-level_domain),
    or an empty string if URL is relative
- `port` -- `None` if absent (or removed)
- `path` -- always with a leading `/`
- `params` -- string of params following the `;` (with extra `;`'s removed)
- `query` -- string of queries following the `?` (with extra `?`'s and `&`'s removed)
- `fragment` -- empty string if absent
- `absolute` -- a `bool` indicating whether the URL is absolute
- `unicode` -- a unicode version of the URL
- `utf8` -- a utf-8 verison of the URL

Contentious Issues
==================
Some questions that I still have outstanding:

Strip ?'s From Query Names?
---------------------------
If I have a query string `?a=1&?b=2`, and I sanitize the params, should the
resulting query string be `?a=1&?b=2` or `?a=1&b=2` (note the missing `?`
before the `b` in the second version).

If not in the above example, what about in `?????a=1`? Should the resulting
query string be a mere `?a=1`?

Properties
----------
I'd like to support lazily-evaluated properties like `hostname`, `netloc`, etc.

Dictionary Access
-----------------
I'd like to support dictionary-style access to parameters and query arguments,
though I'm not sure how to best to do it. My current thinking is that there will
be one way of getting params, one for queries, and then one for either.

Authors
=======
This represents code samples, unit tests and functions from Mozzers,
including:

- David Barts
- Brandon Forehand
- Dan Lecocq
