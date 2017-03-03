#!/usr/bin/env python

# Copyright (c) 2012-2016 SEOmoz, Inc.
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

from distutils.core import setup
from distutils.extension import Extension

ext_files = [
    'url/url-cpp/src/url.cpp',
    'url/url-cpp/src/utf8.cpp',
    'url/url-cpp/src/punycode.cpp',
    'url/url-cpp/src/psl.cpp'
]

kwargs = {}

try:
    from Cython.Distutils import build_ext
    print('Building from Cython')
    ext_files.append('url/url.pyx')
    kwargs['cmdclass'] = {'build_ext': build_ext}
except ImportError:
    print('Building from C++')
    ext_files.append('url/url.cpp')

ext_modules = [
    Extension(
        'url.url', ext_files,
        language='c++',
        extra_compile_args=['-std=c++11'],
        include_dirs=['url/url-cpp/include'])
]

setup(
    name='url',
    version='0.4.1',
    description='URL Parsing',
    long_description='''
Some helper functions for parsing URLs, sanitizing them, normalizing them.

This includes support for escaping, unescaping, punycoding, unpunycoding,
cleaning parameter and query strings, and a little more sanitization.
''',
    author='Dan Lecocq',
    author_email='dan@moz.com',
    url='http://github.com/seomoz/url-py',
    license='MIT',
    platforms='Posix; MacOS X',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    ext_modules=ext_modules,
    packages=[
        'url'
    ],
    package_dir={
        'url': 'url'
    },
    package_data={
        'url': ['psl/*']
    },
    install_requires=[
        'six'
    ],
    tests_require=[
        'coverage',
        'nose'
    ],
    **kwargs
)
