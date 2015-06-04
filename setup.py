#!/usr/bin/env python

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

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name             = 'url',
	version          = '0.1.4',
	description      = 'URL Parsing',
	long_description = '''
Some helper functions for parsing URLs, sanitizing them, normalizing them.

This includes support for escaping, unescaping, punycoding, unpunycoding,
cleaning parameter and query strings, and a little more sanitization.
''',
	author           = 'Dan Lecocq',
	author_email     = 'dan@seomoz.org',
	url              = 'http://github.com/seomoz/url-py',
	py_modules       = ['url'],
	license          = 'MIT',
	platforms        = 'Posix; MacOS X',
	test_suite       = 'tests.testReppy',
	classifiers      = [
		'License :: OSI Approved :: MIT License',
		'Development Status :: 3 - Alpha',
		'Environment :: Web Environment',
		'Intended Audience :: Developers',
		'Topic :: Internet :: WWW/HTTP'],
	install_requires = [
		'coverage',
		'nose',
		'publicsuffix2'
	]
)
