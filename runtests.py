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

import os
import sys
import django
from django.conf import settings


DEFAULT_SETTINGS = dict(
    INSTALLED_APPS = (
        'djangodav',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        # 'djangodav.tests',
    ),
    DATABASES = dict(
        default = dict(
            ENGINE = 'django.db.backends.sqlite3'
        )
    ),
    # ROOT_URLCONF = 'djangodav.tests.urls',
    MIDDLEWARE_CLASSES = (),
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
        },
    ]
)


def runtests(*test_args):
    if not settings.configured:
        settings.configure(**DEFAULT_SETTINGS)
    if hasattr(django, 'setup'):
        django.setup()
    if not test_args:
        test_args = ['djangodav']

    parent = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, parent)
    try:
        from django.test.runner import DiscoverRunner
        runner_class = DiscoverRunner
    except ImportError:
        from django.test.simple import DjangoTestSuiteRunner
        runner_class = DjangoTestSuiteRunner
    failures = runner_class(verbosity=1, interactive=True, failfast=False).run_tests(test_args)
    sys.exit(failures)


if __name__ == '__main__':
    runtests()
