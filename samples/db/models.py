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

from django.db import models
from django.utils.timezone import now


class BaseDavModel(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(default=now)
    modified = models.DateTimeField(default=now)

    class Meta:
        abstract = True


class CollectionModel(BaseDavModel):
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)
    size = 0

    class Meta:
        unique_together = (('parent', 'name'),)


class ObjectModel(BaseDavModel):
    parent = models.ForeignKey(CollectionModel, blank=True, null=True, on_delete=models.CASCADE)
    size = models.IntegerField(default=0)
    content = models.TextField(default=u"")
    md5 = models.CharField(max_length=255)

    class Meta:
        unique_together = (('parent', 'name'),)
