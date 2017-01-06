#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pkgutil
import unittest

import six
from nose.tools import assert_equal, assert_not_equal, assert_raises, assert_is_instance

import url
from url.url import StringURL, UnicodeURL


def test_bad_port():
    def test(example):
        assert_raises(ValueError, url.parse, example)

    examples = [
        'http://www.python.org:65536/',
        'http://www.python.org:-20/',
        'http://www.python.org:8589934592/',
        'http://www.python.org:80hello/'
    ]
    for example in examples:
        yield test, example


def test_deparam_sane():
    def test(bad, good):
        assert_equal(url.parse(bad).strip().deparam(['c']).unicode, good)

    examples = [
        ('?a=1&b=2&c=3&d=4', '?a=1&b=2&d=4'),   # Maintains order
        ('?a=1&&&&&&b=2'   , '?a=1&b=2'    ),   # Removes excess &'s
        (';a=1;b=2;c=3;d=4', ';a=1;b=2;d=4'),   # Maintains order
        (';a=1;;;;;;b=2'   , ';a=1;b=2'    ),   # Removes excess ;'s
        (';foo_c=2'        , ';foo_c=2'    ),   # Not overzealous
        ('?foo_c=2'        , '?foo_c=2'    ),   # ...
        ('????foo=2'       , '?foo=2'      ),   # Removes leading ?'s
        (';foo'            , ';foo'        ),
        ('?foo'            , '?foo'        ),
        (''                , ''            )
    ]
    base = 'http://testing.com/page'
    for bad, good in examples:
        bad = base + bad
        good = base + good
        yield test, bad, good


def test_deparam_case_insensitivity():
    def test(bad, good):
        assert_equal(url.parse(bad).deparam(['HeLlO']).unicode, good)

    examples = [
        ('?hELLo=2', ''),
        ('?HELLo=2', '')
    ]
    base = 'http://testing.com/page'
    for bad, good in examples:
        bad = base + bad
        good = base + good
        yield test, bad, good


def test_filter_params():
    def function(name, value):
        '''Only keep even-valued parameters.'''
        return int(value) % 2

    def test(bad, good):
        assert_equal(url.parse(bad).filter_params(function).unicode, good)

    examples = [
        ('?a=1&b=2', '?b=2'),
        (';a=1;b=2', ';b=2')
    ]
    base = 'http://testing.com/page'
    for bad, good in examples:
        bad = base + bad
        good = base + good
        yield test, bad, good


def test_lower():
    def test(bad, good):
        assert_equal(url.parse(bad).unicode, good)

    examples = [
        ('www.TESTING.coM'    , 'www.testing.com/'   ),
        ('WWW.testing.com'    , 'www.testing.com/'   ),
        ('WWW.testing.com/FOO', 'www.testing.com/FOO')
    ]
    for bad, good in examples:
        bad = 'http://' + bad
        good = 'http://' + good
        yield test, bad, good


def test_abspath():
    def test(bad, good):
        assert_equal(url.parse(bad).abspath().unicode, good)

    examples = [
        ('howdy'           , 'howdy'        ),
        ('hello//how//are' , 'hello/how/are'),
        ('hello/../how/are', 'how/are'      ),
        ('hello//..//how/' , 'how/'         ),
        ('a/b/../../c'     , 'c'            ),
        ('../../../c'      , 'c'            ),
        ('./hello'         , 'hello'        ),
        ('./././hello'     , 'hello'        ),
        ('a/b/c/'          , 'a/b/c/'       ),
        ('a/b/c/..'        , 'a/b/'         ),
        ('a/b/.'           , 'a/b/'         ),
        ('a/b/./././'      , 'a/b/'         ),
        ('a/b/../'         , 'a/'           ),
        ('.'               , ''             ),
        ('../../..'        , ''             ),
        ('////foo'         , 'foo'          ),
        ('/foo/../whiz.'   , 'whiz.'        ),
        ('/foo/whiz./'     , 'foo/whiz./'   ),
        ('/foo/whiz./bar'  , 'foo/whiz./bar')
    ]

    base = 'http://testing.com/'
    for bad, good in examples:
        bad = base + bad
        good = base + good
        yield test, bad, good


def test_escape():
    def test(bad, good):
        assert_equal(url.parse(bad).escape().unicode, good)
        # Escaping should also be idempotent
        assert_equal(url.parse(bad).escape().escape().unicode, good)

    examples = [
        ('hello%20and%20how%20are%20you', 'hello%20and%20how%20are%20you'),
        ('danny\'s pub'                 , 'danny\'s%20pub'               ),
        ('danny%27s pub'                , 'danny\'s%20pub'               ),
        ('danny\'s pub?foo=bar&yo'      , 'danny\'s%20pub?foo=bar&yo'    ),
        ('hello%2c world'               , 'hello,%20world'               ),
        ('%3f%23%5b%5d'                 , '%3F%23%5B%5D'                 ),
        # Thanks to @myronmarston for these test cases
        ('foo?bar none=foo bar'         , 'foo?bar%20none=foo%20bar'     ),
        ('foo;a=1;b=2?a=1&b=2'          , 'foo;a=1;b=2?a=1&b=2'          ),
        ('foo?bar=["hello","howdy"]'    ,
            'foo?bar=%5B%22hello%22,%22howdy%22%5D'),
        # Example from the wild
        ('http://www.balset.com/DE3FJ4Yg/p:h=300&m=2011~07~25~2444705.png&ma=cb&or=1&w=400/2011/10/10/2923710.jpg',
            'http://www.balset.com/DE3FJ4Yg/p:h=300&m=2011~07~25~2444705.png&ma=cb&or=1&w=400/2011/10/10/2923710.jpg'),
        # Example with userinfo
        ('http://user%3Apass@foo.com/', 'http://user:pass@foo.com/')
    ]

    base = 'http://testing.com/'
    for bad, good in examples:
        bad = base + bad
        good = base + good
        yield test, bad, good


def test_strict_escape():
    def test(bad, good):
        assert_equal(url.parse(bad).escape(strict=True).unicode, good)
        # Escaping should also be idempotent
        assert_equal(
            url.parse(bad).escape(strict=True).escape(strict=True).unicode, good)

    examples = [
        ('http://testing.com/danny%27s pub',
            'http://testing.com/danny%27s%20pub'),
        ('http://testing.com/this%5Fand%5Fthat',
            'http://testing.com/this_and_that'),
        ('http://user:pass@foo.com',
            'http://user:pass@foo.com/'),
        (u'http://José:no way@foo.com',
            'http://Jos%C3%A9:no%20way@foo.com/'),
        ('http://oops!:don%27t@foo.com',
            'http://oops!:don%27t@foo.com/'),
        (u'española,nm%2cusa.html?gunk=junk+glunk&foo=bar baz',
            'espa%C3%B1ola,nm%2Cusa.html?gunk=junk+glunk&foo=bar%20baz'),
        ('http://foo.com/bar\nbaz.html\n',
            'http://foo.com/bar%0Abaz.html%0A'),
        ('http://foo.com/bar.jsp?param=\n/value%2F',
            'http://foo.com/bar.jsp?param=%0A/value%2F'),
        ('http://user%3apass@foo.com/',
            'http://user%3Apass@foo.com/')
    ]

    for bad, good in examples:
        yield test, bad, good


def test_userinfo():
    def test(bad, good):
        assert_equal(url.parse(bad).unicode, good)

    examples = [
        ('http://user:pass@foo.com',   'http://user:pass@foo.com'),
        ('http://just-a-name@foo.com', 'http://just-a-name@foo.com')
    ]
    suffix = '/page.html'
    for bad, good in examples:
        bad = bad + suffix
        good = good + suffix
        yield test, bad, good


def test_not_equal():
    def test(first, second):
        # None of these examples should evaluate as strictly equal
        assert_not_equal(url.parse(first), url.parse(second),
            'URL(%s) should not equal URL(%s)' % (first, second))
        # Using a string
        assert_not_equal(url.parse(first), second,
            'URL(%s) should not equal %s' % (first, second))
        # Symmetric
        assert_not_equal(url.parse(second), url.parse(first),
            'URL(%s) should not equal URL(%s)' % (second, first))
        # Using a string, symmetric
        assert_not_equal(url.parse(second), first,
            'URL(%s) should not equal %s' % (second, first))
        # Should equal self
        assert_equal(url.parse(first), first,
            'URL(%s) should equal itself' % first)
        assert_equal(url.parse(second), second,
            'URL(%s) should equal itself' % second)

    # These examples should not work. This includes all the examples from equivalence
    # test as well.
    examples = [
        ('http://foo.com:80'         , 'http://foo.com/'               ),
        ('https://foo.com:443'       , 'https://foo.com/'              ),
        ('http://foo.com/?b=2&&&&a=1', 'http://foo.com/?a=1&b=2'       ),
        ('http://foo.com/%A2%B3'     , 'http://foo.com/%a2%b3'         ),
        ('http://foo.com/a/../b/.'   , 'http://foo.com/b/'             ),
        (u'http://www.kündigen.de/'  , 'http://www.xn--kndigen-n2a.de/'),
        (u'http://www.kündiGen.DE/'  , 'http://www.xn--kndigen-n2a.de/'),
        ('http://foo.com:'           , 'http://foo.co.uk/'             ),
        ('http://foo.com:8080'       , 'http://foo.com/'               ),
        ('https://foo.com:4430'      , 'https://foo.com/'              ),
        ('http://foo.com?page&foo'   , 'http://foo.com/?page'          ),
        ('http://foo.com/?b=2&c&a=1' , 'http://foo.com/?a=1&b=2'       ),
        ('http://foo.com/%A2%B3%C3'  , 'http://foo.com/%a2%b3'         ),
        (u'http://www.kündïgen.de/'  , 'http://www.xn--kndigen-n2a.de/'),
        ('http://user:pass@foo.com/' , 'http://foo.com/'               ),
        ('http://just-user@foo.com/' , 'http://foo.com/'               ),
        ('http://user:pass@foo.com/' , 'http://pass:user@foo.com/'     )
    ]
    for first, second in examples:
        yield test, first, second


def test_equiv():
    def test(first, second):
        # Equiv with another URL object
        assert url.parse(first).equiv(url.parse(second))
        # Equiv with a string
        assert url.parse(first).equiv(second)
        # Make sure it's also symmetric
        assert url.parse(second).equiv(url.parse(first))
        # Symmetric with string arg
        assert url.parse(second).equiv(first)
        # Should be equivalent to self
        assert url.parse(first).equiv(first)
        assert url.parse(second).equiv(second)

    # Things to consider here are:
    #
    #   - default ports (https://foo.com/ == https://foo.com:443/)
    #   - capitalization of the hostname
    #   - capitalization of the escaped characters in the path
    examples = [
        ('http://foo.com:80'         , 'http://foo.com/'               ),
        ('https://foo.com:443'       , 'https://foo.com/'              ),
        ('http://foo.com/?b=2&&&&a=1', 'http://foo.com/?a=1&b=2'       ),
        ('http://foo.com/%A2%B3'     , 'http://foo.com/%a2%b3'         ),
        ('http://foo.com/a/../b/.'   , 'http://foo.com/b/'             ),
        (u'http://www.kündigen.de/'  , 'http://www.xn--kndigen-n2a.de/'),
        (u'http://www.kündiGen.DE/'  , 'http://www.xn--kndigen-n2a.de/'),
        ('http://user:pass@foo.com/' , 'http://foo.com/'               ),
        ('http://just-user@foo.com/' , 'http://foo.com/'               )
    ]

    for first, second in examples:
        yield test, first, second


def test_not_equiv():
    def test(first, second):
        # Equiv with another URL object
        assert not url.parse(first).equiv(url.parse(second))
        # Equiv with a string
        assert not url.parse(first).equiv(second)
        # Make sure it's also symmetric
        assert not url.parse(second).equiv(url.parse(first))
        # Symmetric with string arg
        assert not url.parse(second).equiv(first)
        # Should be equivalent to self
        assert url.parse(first).equiv(first)
        assert url.parse(second).equiv(second)

        # None of these examples should evaluate as strictly equal
        assert_not_equal(url.parse(first), url.parse(second),
            'URL(%s) should not equal URL(%s)' % (first, second))
        # Using a string
        assert_not_equal(url.parse(first), second,
            'URL(%s) should not equal %s' % (first, second))
        # Symmetric
        assert_not_equal(url.parse(second), url.parse(first),
            'URL(%s) should not equal URL(%s)' % (second, first))
        # Using a string, symmetric
        assert_not_equal(url.parse(second), first,
            'URL(%s) should not equal %s' % (second, first))
        # Should equal self
        assert_equal(url.parse(first), first,
            'URL(%s) should equal itself' % first)
        assert_equal(url.parse(second), second,
            'URL(%s) should equal itself' % second)

    # Now some examples that should /not/ pass
    examples = [
        ('http://foo.com:'           , 'http://foo.co.uk/'             ),
        ('http://foo.com:8080'       , 'http://foo.com/'               ),
        ('https://foo.com:4430'      , 'https://foo.com/'              ),
        ('http://foo.com?page&foo'   , 'http://foo.com/?page'          ),
        ('http://foo.com/?b=2&c&a=1' , 'http://foo.com/?a=1&b=2'       ),
        ('http://foo.com/%A2%B3%C3'  , 'http://foo.com/%a2%b3'         ),
        (u'http://www.kündïgen.de/'  , 'http://www.xn--kndigen-n2a.de/')
    ]

    for first, second in examples:
        yield test, first, second


def test_str_repr():
    def test(first, second):
        assert_equal(str(url.parse(toparse)), strng)
        assert_equal(repr(url.parse(toparse)),
            '<url.URL object "%s" >' % strng)

    examples = [
        ('http://foo.com/', 'http://foo.com/'),
        ('http://FOO.com/', 'http://foo.com/')
    ]

    for toparse, strng in examples:
        yield test, toparse, strng


def test_canonical():
    def test(bad, good):
        assert_equal(url.parse(bad).canonical().unicode, good)

    examples = [
        ('?b=2&a=1&c=3', '?a=1&b=2&c=3'),
        (';b=2;a=1;c=3', ';a=1;b=2;c=3')
    ]

    base = 'http://testing.com/'
    for bad, good in examples:
        bad = base + bad
        good = base + good
        yield test, bad, good


def test_defrag():
    def test(bad, good):
        assert_equal(url.parse(bad).defrag().unicode, good)

    examples = [
        ('foo#bar', 'foo')
    ]

    base = 'http://testing.com/'
    for bad, good in examples:
        bad = base + bad
        good = base + good
        yield test, bad, good


def test_deuserinfo():
    def test(bad, good):
        assert_equal(url.parse(bad).deuserinfo().unicode, good)

    examples = [
        ('http://user:pass@foo.com/', 'http://foo.com/'),
        ('http://just-user@foo.com/', 'http://foo.com/')
    ]
    for bad, good in examples:
        yield test, bad, good


def test_punycode():
    def test(uni, puny):
        assert_equal(url.parse(uni).escape().punycode().unicode, puny)
        # Also make sure punycode is idempotent
        assert_equal(
            url.parse(uni).escape().punycode().punycode().unicode, puny)
        # Make sure that we can reverse the procedure correctly
        assert_equal(
            url.parse(uni).escape().punycode().unpunycode().unescape(),
            uni)
        # And we get what we'd expect going the opposite direction
        assert_equal(
            url.parse(puny).unescape().unpunycode().unicode, uni)

    examples = [
        (u'http://www.kündigen.de/',
            'http://www.xn--kndigen-n2a.de/'),
        (u'http://россия.иком.museum/',
            'http://xn--h1alffa9f.xn--h1aegh.museum/'),
        (u'https://t…/',
            'https://xn--t-9hn/'),
        (u'http://россия.иком.museum/испытание.html',
            'http://xn--h1alffa9f.xn--h1aegh.museum/%D0%B8%D1%81%D0%BF%D1%8B%D1%82%D0%B0%D0%BD%D0%B8%D0%B5.html')
    ]

    for uni, puny in examples:
        yield test, uni, puny


def test_punycode_relative_urls():
    def test(example):
        assert_equal(url.parse(example).escape().punycode().unicode, example)
        # Also make sure punycode is idempotent
        assert_equal(
            url.parse(example).escape().punycode().punycode().unicode, example)
        # Make sure that we can reverse the procedure correctly
        assert_equal(
            url.parse(example).escape().punycode().unpunycode().unescape(),
            example)
        # And we get what we'd expect going the opposite direction
        assert_equal(
            url.parse(example).unescape().unpunycode().unicode, example)

    # Make sure that we can't punycode or unpunycode relative urls
    examples = ['foo', '../foo', '/bar/foo']
    for relative in examples:
        yield test, relative


def test_punycode_encode_errors():
    def test(example):
        assert_raises(ValueError, url.parse('http://' + example).punycode)

    # Taken from url-cpp
    examples = [
        (('a' * 3855) + '\xF4\x8F\xBF\xBF'),
        (('a' * 8190) + '\xC2\x80\xF2\x80\x82\x80')
    ]

    for example in examples:
        yield test, example


def test_segment_lengths():
    def test(example):
        assert_raises(ValueError, url.parse(example).punycode)

    examples = [
        'http://foo..com/',
        'http://foo../',
        'http://this-is-a-very-long-segment-that-has-more-than-sixty-three-characters.com/',
        'http://this-is-a-very-long-segment-that-has-more-than-sixty-three-characters/'
    ]

    for example in examples:
        yield test, example

def test_punycode_decode_errors():
    def test(example):
        assert_raises(ValueError, url.parse('http://xn--' + example).unpunycode)

    # Taken from url-cpp
    examples = [
        'd9juau41awczcz',
        '\xc3\xbc-',
        's121kz41webp2qdk6492joxumu36',
        '999999b'
    ]

    for example in examples:
        yield test, example


def test_relative():
    def test(rel, absolute):
        assert_equal(base.relative(rel).unicode, absolute)

    base = url.parse('http://testing.com/a/b/c')
    examples = [
        ('../foo'            , 'http://testing.com/a/foo'     ),
        ('./foo'             , 'http://testing.com/a/b/foo'   ),
        ('foo'               , 'http://testing.com/a/b/foo'   ),
        ('/foo'              , 'http://testing.com/foo'       ),
        ('http://foo.com/bar', 'http://foo.com/bar'           ),
        ('/foo'              , 'http://testing.com/foo'       ),
        (u'/\u200Bfoo'       , u'http://testing.com/\u200Bfoo'),
        ('../../../../'      , 'http://testing.com/'          ),
        (u'http://www\u200B.tiagopriscostudio.com',
            u'http://www\u200B.tiagopriscostudio.com/')
    ]

    for rel, absolute in examples:
        yield test, rel, absolute


def test_relative_javascript():
    rel = 'javascript:console.log("hello")'
    base = 'http://foo.com/path'
    assert_equal(rel, url.parse(rel).relative_to(base).unicode)


def test_sanitize():
    def test(bad, good):
        assert_equal(url.parse(bad).sanitize().unicode, good)

    examples = [
        ('../foo/bar none', 'foo/bar%20none')
    ]

    base = 'http://testing.com/'
    for bad, good in examples:
        bad = base + bad
        good = base + good
        yield test, bad, good


def test_remove_default_port():
    def test(query, result):
        assert_equal(url.parse(query).remove_default_port().unicode, result)

    examples = [
        ('http://foo.com:80/'  , 'http://foo.com/'     ),
        ('https://foo.com:443/', 'https://foo.com/'    ),
        ('http://foo.com:8080/', 'http://foo.com:8080/')
    ]

    for query, result in examples:
        yield test, query, result


def test_absolute():
    def test(query, result):
        assert_equal(url.parse(query).absolute, result)

    examples = [
        ('http://foo.com/bar', True ),
        ('foo/'              , False),
        ('http://foo.com'    , True ),
        ('/foo/bar/../'      , False)
    ]

    for query, result in examples:
        yield test, query, result


def test_hostname():
    def test(query, result):
        assert_equal(url.parse(query).hostname, result)

    examples = [
        ('http://foo.com/bar',     'foo.com'),
        ('http://bar.foo.com/bar', 'bar.foo.com'),
        ('/foo',                   '')
    ]
    for query, result in examples:
        yield test, query, result


def test_pld():
    def test(query, result):
        assert_equal(url.parse(query).pld, result)

    examples = [
        ('http://foo.com/bar'     , 'foo.com'),
        ('http://bar.foo.com/bar' , 'foo.com'),
        ('/foo'                   , ''),
        ('http://com/bar'         , ''),
        ('http://foo.გე'          , 'foo.გე'),
        ('http://bar.foo.გე'      , 'foo.გე'),
        ('http://foo.xn--node'    , 'foo.xn--node'),
        ('http://bar.foo.xn--node', 'foo.xn--node'),
        ('http://foo.co.uk'       , 'foo.co.uk')
    ]
    for query, result in examples:
        yield test, query, result


def test_tld():
    def test(query, result):
        assert_equal(url.parse(query).tld, result)

    examples = [
        ('http://foo.com/bar'    , 'com'),
        ('http://bar.foo.com/bar', 'com'),
        ('/foo'                  , ''),
        ('http://com/bar'        , 'com'),
        ('http://foo.გე'          , 'გე'),
        ('http://bar.foo.გე'      , 'გე'),
        ('http://foo.xn--node'    , 'xn--node'),
        ('http://bar.foo.xn--node', 'xn--node'),
        ('http://foo.co.uk'       , 'co.uk')
    ]
    for query, result in examples:
        yield test, query, result


def test_empty_hostname():
    def test(example):
        # Equal to itself
        assert_equal(url.parse(example), example)
        # String representation equal to the provided example
        assert_equal(url.parse(example).unicode, example)

    examples = [
        'http:///path',
        'http://userinfo@/path',
        'http://:80/path',
    ]
    for example in examples:
        yield test, example

def test_copy():
    def test(example):
        original = url.parse(example)
        copy = original.copy()
        assert_equal(original, copy)
        assert_not_equal(id(original), id(copy))

    examples = [
        'http://testing.com/danny%27s pub',
        'http://testing.com/this%5Fand%5Fthat',
        'http://user:pass@foo.com',
        u'http://José:no way@foo.com',
        'http://oops!:don%27t@foo.com'
        u'española,nm%2cusa.html?gunk=junk+glunk&foo=bar baz',
        'http://foo.com/bar\nbaz.html\n',
        'http://foo.com/bar.jsp?param=\n/value%2F',
        'http://user%3apass@foo.com/'
    ]
    for example in examples:
        yield test, example

def test_set_psl():
    '''Can set the PSL to use.'''

    def test(rules, example, pld, tld):
        try:
            url.set_psl(rules)
            assert_equal(url.parse(example).pld, pld)
            assert_equal(url.parse(example).tld, tld)
        finally:
            url.set_psl(pkgutil.get_data('url', 'psl/2016-08-16.psl'))

    examples = [
        ('uk',    'http://foo.co.uk/', 'co.uk',     'uk'   ),
        ('co.uk', 'http://foo.co.uk/', 'foo.co.uk', 'co.uk')
    ]

    for rules, example, pld, tld in examples:
        yield test, rules, example, pld, tld

def test_tel():
    '''Can parse tel links properly.'''
    parsed = url.parse('tel:0108202201')
    assert_equal(parsed.scheme, 'tel')
    assert_equal(parsed.path, '0108202201')

def test_unknown_protocol():
    '''Can parse unknown protocol links.'''
    parsed = url.parse('unknown:0108202201')
    assert_equal(parsed.scheme, '')
    assert_equal(parsed.path, 'unknown:0108202201')


def test_component_assignment():
    parsed = url.parse('http://user@example.com:80/path;params?query#fragment')
    parsed.scheme = 'https'
    parsed.userinfo = 'username'
    parsed.host = 'foo.example.com'
    parsed.port = 443
    parsed.path = '/another/path'
    parsed.params = 'no-params'
    parsed.query = 'no-query'
    parsed.fragment = 'no-fragment'
    assert_equal(
        parsed.unicode, 
        'https://username@foo.example.com:443/another/path;no-params?no-query#no-fragment'
    )

def test_component_assignment_unicode():
    parsed = url.parse('http://user@example.com:80/path;params?query#fragment')
    parsed.scheme = u'https'
    parsed.userinfo = u'username'
    parsed.host = u'foo.example.com'
    parsed.port = 443
    parsed.path = u'/another/path'
    parsed.params = u'no-params'
    parsed.query = u'no-query'
    parsed.fragment = u'no-fragment'
    assert_equal(
        parsed.unicode, 
        'https://username@foo.example.com:443/another/path;no-params?no-query#no-fragment'
    )

def test_string_url():
    parsed = StringURL.parse('http://user@example.com:80/path;params?query#fragment')
    properties = [
        'scheme', 'host', 'params', 'query', 'fragment', 'userinfo', 'pld', 'tld'
    ]
    for prop in properties:
        yield assert_is_instance, getattr(parsed, prop), six.binary_type

def test_unicode_url():
    parsed = UnicodeURL.parse('http://user@example.com:80/path;params?query#fragment')
    properties = [
        'scheme', 'host', 'params', 'query', 'fragment', 'userinfo', 'pld', 'tld'
    ]
    for prop in properties:
        yield assert_is_instance, getattr(parsed, prop), six.text_type
