=================
DjangoDav classes
=================


views.DavView
-------------

DavView is responsible for request handling. It routes http methods, and translates xml request body to internal
representation and building xml responses. It uses DavLock class to provide resource locking data management and
DavResource to manage resources.


Locks
-----

base.lock.BaseDavLock
~~~~~~~~~~~~~~~~~~~~~

Provides access to locks data management.

lock.DummyLock
~~~~~~~~~~~~~~

Provides lock emulation.


Resources
---------

Encapsulating storage functionality. Providing public objects management methods and available property list.


base.resource.BaseDavResource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Provides base resource management functionality. Like data conversion and resource copy/move logic.


fs.resource.BaseFSDavResource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides all filesystem operations accept reading and writing files.


fs.resource.DummyWriteFSDavResource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides through memory write to fs.


fs.resource.DummyReadFSDavResource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides through memory read from fs.


fs.resource.SendFileFSDavResource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uses SendFile functionality of Apache or Nginx web-server to provide resource reading.


fs.resource.RedirectFSDavResource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uses X-Redirect functionality of Nginx web-server to provide resource reading.


db.resource.DBBaseResource
~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides base functionality to provide access to database resources.


db.resource.NameLookupDBDavMixIn
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides access to database resources by object names lookup.
