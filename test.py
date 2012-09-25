#! /usr/bin/env python
# -*- coding: utf-8 -*-

import url
import unittest

class Test(unittest.TestCase):
    '''All the tests!'''

    def test_deparam(self):
        '''Even though the spec says that parameter order doesn't matter, it
        can matter in practice. So, we preserve order'''
        examples = [
            ('?a=1&b=2&c=3&d=4', '?a=1&b=2&d=4'),   # Maintains order
            ('?a=1&&&&&&b=2'   , '?a=1&b=2'    ),   # Removes excess &'s
            (';a=1;b=2;c=3;d=4', ';a=1;b=2;d=4'),   # Maintains order
            (';a=1;;;;;;b=2'   , ';a=1;b=2'    ),   # Removes excess ;'s
            (';foo_c=2'        , ';foo_c=2'    ),   # Not overzealous
            ('?foo_c=2'        , '?foo_c=2'    ),   # ...
            ('????foo=2'       , '?foo=2'      )    # Removes leading ?'s
        ]
        base = 'http://testing.com/page'
        for bad, good in examples:
            bad = base + bad
            good = base + good
            self.assertEqual(url.parse(bad).deparam(['c']).utf8(), good)

    def test_lower(self):
        '''Can lowercase the domain name correctly'''
        examples = [
            ('www.TESTING.coM'    , 'www.testing.com/'   ),
            ('WWW.testing.com'    , 'www.testing.com/'   ),
            ('WWW.testing.com/FOO', 'www.testing.com/FOO')
        ]
        for bad, good in examples:
            bad = 'http://' + bad
            good = 'http://' + good
            self.assertEqual(url.parse(bad).lower().utf8(), good)

    def test_abspath(self):
        '''Make sure absolute path checking works correctly'''
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
            ('////foo'         , 'foo'          )
        ]

        base = 'http://testing.com/'
        for bad, good in examples:
            bad = base + bad
            good = base + good
            self.assertEqual(url.parse(bad).abspath().utf8(), good)

    def test_escape(self):
        '''Make sure we escape paths correctly'''
        examples = [
            ('hello%20and%20how%20are%20you', 'hello%20and%20how%20are%20you'),
            ('danny\'s pub'                 , 'danny%27s%20pub'),
            ('danny%27s pub?foo=bar&yo'     , 'danny%27s%20pub?foo=bar&yo')
        ]

        base = 'http://testing.com/'
        for bad, good in examples:
            bad = base + bad
            good = base + good
            self.assertEqual(url.parse(bad).escape().utf8(), good)
            # Escaping should also be idempotent
            self.assertEqual(url.parse(bad).escape().escape().utf8(), good)

    def test_equiv(self):
        '''Make sure equivalent urls work correctly'''
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
        ]

        for first, second in examples:
            # Equiv with another URL object
            self.assertTrue(url.parse(first).equiv(url.parse(second)),
                '%s should equiv(%s)' % (first, second))
            # Equiv with a string
            self.assertTrue(url.parse(first).equiv(second),
                '%s should equiv(%s)' % (first, second))
            # Make sure it's also transitive
            self.assertTrue(url.parse(second).equiv(url.parse(first)),
                '%s should equiv(%s)' % (second, first))
            # Transitive with string arg
            self.assertTrue(url.parse(second).equiv(first),
                '%s should equiv(%s)' % (second, first))
            # Should be equivalent to self
            self.assertTrue(url.parse(first).equiv(first),
                '%s should equiv itself' % first)
            self.assertTrue(url.parse(second).equiv(second),
                '%s should equiv itself' % second)

            # None of these examples should evaluate as strictly equal
            self.assertNotEqual(url.parse(first), url.parse(second),
                'URL(%s) should not equal URL(%s)' % (first, second))
            # Using a string
            self.assertNotEqual(url.parse(first), second,
                'URL(%s) should not equal %s' % (first, second))
            # Transitive
            self.assertNotEqual(url.parse(second), url.parse(first),
                'URL(%s) should not equal URL(%s)' % (second, first))
            # Using a string, transitive
            self.assertNotEqual(url.parse(second), first,
                'URL(%s) should not equal %s' % (second, first))
            # Should equal self
            self.assertEqual(url.parse(first), first,
                'URL(%s) should equal itself' % first)
            self.assertEqual(url.parse(second), second,
                'URL(%s) should equal itself' % second)

        # Now some examples that should /not/ pass
        examples = [
            ('http://foo.com:'           , 'http://foo.co.uk/'             ),
            ('http://foo.com:8080'       , 'http://foo.com/'               ),
            ('https://foo.com:4430'      , 'https://foo.com/'              ),
            ('http://foo.com?page&foo'   , 'http://foo.com/?page'          ),
            ('http://foo.com/?b=2&c&a=1' , 'http://foo.com/?a=1&b=2'       ),
            ('http://foo.com/%A2%B3%C3'  , 'http://foo.com/%a2%b3'         ),
            (u'http://www.kündïgen.de/'  , 'http://www.xn--kndigen-n2a.de/'),
        ]

        for first, second in examples:
            # Equiv with another URL object
            self.assertFalse(url.parse(first).equiv(url.parse(second)),
                '%s should not equiv(%s)' % (first, second))
            # Equiv with a string
            self.assertFalse(url.parse(first).equiv(second),
                '%s should not equiv(%s)' % (first, second))
            # Make sure it's also transitive
            self.assertFalse(url.parse(second).equiv(url.parse(first)),
                '%s should not equiv(%s)' % (second, first))
            # Transitive with string arg
            self.assertFalse(url.parse(second).equiv(first),
                '%s should not equiv(%s)' % (second, first))
            # Should be equivalent to self
            self.assertTrue(url.parse(first).equiv(first),
                '%s should equiv itself' % first)
            self.assertTrue(url.parse(second).equiv(second),
                '%s should equiv itself' % second)

            # None of these examples should evaluate as strictly equal
            self.assertNotEqual(url.parse(first), url.parse(second),
                'URL(%s) should not equal URL(%s)' % (first, second))
            # Using a string
            self.assertNotEqual(url.parse(first), second,
                'URL(%s) should not equal %s' % (first, second))
            # Transitive
            self.assertNotEqual(url.parse(second), url.parse(first),
                'URL(%s) should not equal URL(%s)' % (second, first))
            # Using a string, transitive
            self.assertNotEqual(url.parse(second), first,
                'URL(%s) should not equal %s' % (second, first))
            # Should equal self
            self.assertEqual(url.parse(first), first,
                'URL(%s) should equal itself' % first)
            self.assertEqual(url.parse(second), second,
                'URL(%s) should equal itself' % second)

    def test_str_repr(self):
        '''Make sure str and repr produce reasonable results'''
        examples = [
            ('http://foo.com/', 'http://foo.com/'),
            ('http://FOO.com/', 'http://foo.com/')
        ]

        for toparse, strng in examples:
            self.assertEqual(str(url.parse(toparse)), strng)
            self.assertEqual(repr(url.parse(toparse)),
                '<url.URL object "%s" >' % strng)

    def test_canonical(self):
        '''Correctly canonicalizes urls'''
        examples = [
            ('?b=2&a=1&c=3', '?a=1&b=2&c=3'),
            (';b=2;a=1;c=3', ';a=1;b=2;c=3')
        ]

        base = 'http://testing.com/'
        for bad, good in examples:
            bad = base + bad
            good = base + good
            self.assertEqual(url.parse(bad).canonical().utf8(), good)

    def test_defrag(self):
        '''Correctly defrags urls'''
        examples = [
            ('foo#bar', 'foo')
        ]

        base = 'http://testing.com/'
        for bad, good in examples:
            bad = base + bad
            good = base + good
            self.assertEqual(url.parse(bad).defrag().utf8(), good)

    def test_punycode(self):
        '''Make sure punycode encoding works correctly'''
        examples = [
            (u'http://www.kündigen.de/',
                'http://www.xn--kndigen-n2a.de/'),
            (u'http://россия.иком.museum/',
                'http://xn--h1alffa9f.xn--h1aegh.museum/'),
            (u'http://россия.иком.museum/испытание.html',
                'http://xn--h1alffa9f.xn--h1aegh.museum/%D0%B8%D1%81%D0%BF%D1%8B%D1%82%D0%B0%D0%BD%D0%B8%D0%B5.html')
        ]

        for uni, puny in examples:
            self.assertEqual(url.parse(uni).escape().punycode().utf8(), puny)
            # Also make sure punycode is idempotent
            self.assertEqual(
                url.parse(uni).escape().punycode().punycode().utf8(), puny)
            # Make sure that we can reverse the procedure correctly
            self.assertEqual(
                url.parse(uni).escape().punycode().unpunycode().unescape(),
                uni)
            # And we get what we'd expect going the opposite direction
            self.assertEqual(
                url.parse(puny).unescape().unpunycode().unicode(), uni)

        # Make sure that we can't punycode or unpunycode relative urls
        examples = ['foo', '../foo', '/bar/foo']
        for relative in examples:
            self.assertRaises(TypeError, url.parse(relative).punycode)
            self.assertRaises(TypeError, url.parse(relative).unpunycode)

    def test_relative(self):
        '''Test relative url parsing'''
        base = url.parse('http://testing.com/a/b/c')
        examples = [
            ('../foo'            , 'http://testing.com/a/foo'  ),
            ('./foo'             , 'http://testing.com/a/b/foo'),
            ('foo'               , 'http://testing.com/a/b/foo'),
            ('/foo'              , 'http://testing.com/foo'    ),
            ('http://foo.com/bar', 'http://foo.com/bar'        ),
            (u'/foo'             , 'http://testing.com/foo'    )
        ]

        for rel, absolute in examples:
            self.assertEqual(base.relative(rel).utf8(), absolute)

    def test_sanitize(self):
        '''Make sure the sanitize method does all that it should'''
        examples = [
            ('../foo/bar none', 'foo/bar%20none')
        ]

        base = 'http://testing.com/'
        for bad, good in examples:
            bad = base + bad
            good = base + good
            self.assertEqual(url.parse(bad).sanitize().utf8(), good)

    def test_absolute(self):
        '''Can it recognize if it's a relative or absolute url?'''
        examples = [
            ('http://foo.com/bar', True ),
            ('foo/'              , False),
            ('http://foo.com'    , True ),
            ('/foo/bar/../'      , False)
        ]

        for query, result in examples:
            self.assertEqual(url.parse(query).absolute(), result)


if __name__ == '__main__':
    unittest.main()
