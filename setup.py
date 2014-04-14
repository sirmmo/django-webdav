#!/usr/bin/env python
#
# Portions (c) 2014, Alexander Klimenko <alex@erix.ru>
# All rights reserved.
#
# Copyright (c) 2011, SmartFile <btimby@smartfile.com>
# All rights reserved.
#
# This file is part of DjangoDav.
#
# DjangoDav is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DjangoDav is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with DjangoDav.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup

setup(
    name='DjangoDav',
    version='0.0.1',
    description=('A WebDAV server for Django.'),
    long_description=(
"""
Fork of WebDAV implemented as a Django application. The motivation for this project is to
allow authentication of users against Django's contrib.auth system, while also
exporting different directories per user. Many Django tools and app can be combined
with this such as django-digest etc. to provide a powerful WebDAV server. 
"""
    ),
    author='Alexander Klimenko',
    author_email='alex@erix.ru',
    url='https://github.com/meteozond/djangodav',
    packages=['djangodav'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    include_package_data=True,
    zip_safe=False,
    test_suite='runtests.runtests'
)
