---------------------------------------
Difference with SmartFile django-webdav
---------------------------------------

Base resource functionality was separated into BaseResource class from the storage
functionality which developers free to choose from provided or implement themselves.

Improved class dependencies. Resource class don’t know anything about url or server, its
goal is only to store content and provide proper access.

Removed properties helper class. View is now responsible for xml generation, and resource
provides actual property list.

Server is now inherited from Django Class Based View, and renamed to DavView.

Key methods covered with tests.

Removed redundant request handler.

Added FSResource and DBResource to provide file system and data base access.

Xml library usage is replaced with lxml to achieve proper xml generation code readability.
