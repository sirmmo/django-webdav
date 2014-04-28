============
Known issues
============


Recreating collection on move
-----------------------------

To provide easier usage we encapsulated highlevel copy and move methods, which provide graceful conflict resolution
and don't know anything about end data representation, at the same time. If you need to provide native move, you can
override these methods.

Revert on error
---------------

Webdav standart expects that all changes will be reverted if the operation can't be finished. Now it can be provided by
DBResource with transaction based database. FSResource does't support transactions of any kind.
