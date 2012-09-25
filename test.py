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
            ('a/b/c/'          , 'a/b/c/'       )
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
            ('http://foo.com:'           , 'http://foo.com/'        ),
            ('http://foo.com:80'         , 'http://foo.com/'        ),
            ('https://foo.com:443'       , 'https://foo.com/'       ),
            ('http://foo.COM/'           , 'http://foo.com/'        ),
            ('http://foo.com?page'       , 'http://foo.com/?page'   ),
            ('http://foo.com/?b=2&&&&a=1', 'http://foo.com/?a=1&b=2'),
            ('http://foo.com/%A2%B3'     , 'http://foo.com/%a2%b3'  )
        ]

        for first, second in examples:
            self.assertTrue(url.parse(first).equiv(url.parse(second)),
                '%s should equiv(%s)' % (first, second))

    def test_punycode(self):
        '''Make sure punycode encoding works correctly'''
        examples = [
            (u'http://www.kündigen.de',
                'http://www.xn--kndigen-n2a.de/'),
            (u'http://россия.иком.museum',
                'http://xn--h1alffa9f.xn--h1aegh.museum/'),
            (u'http://россия.иком.museum/испытание.html',
                'http://xn--h1alffa9f.xn--h1aegh.museum/%D0%B8%D1%81%D0%BF%D1%8B%D1%82%D0%B0%D0%BD%D0%B8%D0%B5.html')
        ]

        for bad, good in examples:
            self.assertEqual(url.parse(bad).escape().punycode().utf8(), good)
            # Also make sure punycode is idempotent
            self.assertEqual(
                url.parse(bad).escape().punycode().punycode().utf8(), good)

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

    def test_unpunycode(self):
        '''Unpunycode a url'''
        examples = [
            (u'http://www.kündigen.de/',
                'http://www.xn--kndigen-n2a.de/'),
            (u'http://россия.иком.museum/',
                'http://xn--h1alffa9f.xn--h1aegh.museum/'),
            (u'http://россия.иком.museum/испытание.html',
                'http://xn--h1alffa9f.xn--h1aegh.museum/%D0%B8%D1%81%D0%BF%D1%8B%D1%82%D0%B0%D0%BD%D0%B8%D0%B5.html')
        ]

        for uni, puny in examples:
            self.assertEqual(
                url.parse(puny).unescape().unpunycode().unicode(), uni)

    def test_relative(self):
        '''Test relative url parsing'''
        base = url.parse('http://testing.com/a/b/c')
        examples = [
            ('../foo'            , 'http://testing.com/a/b/foo'  ),
            ('./foo'             , 'http://testing.com/a/b/c/foo'),
            ('foo'               , 'http://testing.com/a/b/c/foo'),
            ('/foo'              , 'http://testing.com/foo'      ),
            ('http://foo.com/bar', 'http://foo.com/bar'          )
        ]

        for rel, absolute in examples:
            self.assertEqual(base.relative(rel), absolute)


if __name__ == '__main__':
    unittest.main()
