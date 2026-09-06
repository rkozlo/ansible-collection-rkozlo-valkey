========================================================
Ansible rkozlo.valkey collection changelog Release Notes
========================================================

.. contents:: Topics

v0.4.0
======

Release Summary
---------------

This is minor release of the collection.

Minor Changes
-------------

- valkey_client - lazy load client. Allows module to handle on its own library exceptions.

New Modules
-----------

- valkey_wait - Wait until Valkey will be in certain condition.

v0.3.1
======

Release Summary
---------------

Bugfix building tarbal.

Bugfixes
--------

- Fix build collection. Lack files in manifest.

v0.3.0
======

Release Summary
---------------

Introduce first version of cluster option. Basic cluster commands are supported now.

Minor Changes
-------------

- Add cluster option to enable cluster mode. It will allow execute cluster_* methods with valkey_exec.
- Option login_db required false from now.

v0.2.0
======

Minor Changes
-------------

- valkey_user - add option save_acls and enable this as default.

v0.1.0
======

Release Summary
---------------

This is the first release of the rkozlo.valkey collection.

Minor Changes
-------------

- valkey_exec - add the module.
- valkey_info - add the module.
- valkey_user - add the module.
