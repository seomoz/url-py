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

from setuptools import setup
from setuptools.extension import Extension

ext_files = [
    'url/url-cpp/src/url.cpp',
    'url/url-cpp/src/utf8.cpp',
    'url/url-cpp/src/punycode.cpp',
    'url/url-cpp/src/psl.cpp',
    'url/url.pyx'
]

import sys

extra_args = []
if(sys.platform == 'win32'):
    extra_args.append('/std:c++14')
else:
    extra_args.append('-std=c++11')

ext_modules = [
    Extension(
        'url.url', ext_files,
        language='c++',
        extra_compile_args=extra_args,
        include_dirs=['url/url-cpp/include'])
]

setup(
    ext_modules=ext_modules,
    packages=[ 'url' ],
    package_dir={ 'url': 'url' },
    package_data={ 'url': ['psl/*'] }
)
