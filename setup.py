#!/usr/bin/env python
#
# Copyright (c) 2011, SmartFile <btimby@smartfile.com>
# All rights reserved.
#
# This file is part of django-webdav.
#
# Foobar is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with django-webdav.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup

setup(
    name='django-webdav',
    version='0.1',
    description=('A WebDAV server for Django.'),
    long_description=(
"""
WebDAV implemented as a Django application. The motivation for this project is to
allow authentication of users against Django's contrib.auth system, while also
exporting different directories per user. Many Django tools and app can be combined
with this such as django-digest etc. to provide a powerful WebDAV server. 
"""
    ),
    author='SmartFile',
    author_email='btimby@smartfile.com',
    url='http://code.google.com/p/django-webdav/',
    packages=['django_webdav'],
              #'django_webdav.samples'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
     ],
    zip_safe=False,
)
