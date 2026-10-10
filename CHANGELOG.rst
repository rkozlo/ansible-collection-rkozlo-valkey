========================================================
Ansible rkozlo.valkey collection changelog Release Notes
========================================================

.. contents:: Topics

v0.6.0
======

Release Summary
---------------

This is minor release of collection. Mostly bugfixes and improvements.

Minor Changes
-------------

- all modules - fail with a clear message when ``login_db`` is used together with ``cluster=true``.
- valkey client - use standard ``missing_required_lib`` message with import traceback when the ``valkey`` Python package is missing.
- valkey_config - ``after`` in ``changed_configs`` and ``immutable`` is now always a string.
- valkey_config - fail with a clear message instead of a traceback when the server version or a config is not present in the supported configs table.
- valkey_config - instead of calling CONFIG SET for each config send it only once passing all of the settings atomically.
- valkey_config - support diff mode. With ``--diff`` before and after values of changed configs are shown.

Breaking Changes / Porting Guide
--------------------------------

- valkey_config - return value ``diff`` was renamed to ``changed_configs``. ``diff`` is reserved by Ansible for diff mode.

Bugfixes
--------

- valkey client - do not report internal ``AttributeError`` as an unsupported command. Unknown commands now report the missing method in valkey-py.
- valkey client - handle timeouts, lost connections and other Valkey errors during command execution with a clear message instead of a traceback.
- valkey client - report authentication failures as such instead of a generic connection error.
- valkey_config - remove redundant config rewrite. Execute only once if any config has changed.
- valkey_exec - report invalid arguments for a command with a clear message instead of a traceback.
- valkey_user - accept uppercase ``hashed_passwords`` by lowercasing them and fix deduplication of passwords and hashes.
- valkey_user - do not execute ``ACL SAVE`` on user creation when ``save_acls`` is false.
- valkey_user - fail early when ``save_acls`` is enabled but the server has no aclfile configured (check was never executed).
- valkey_user - strip leading ``&`` from ``channels``. Previously it was sent as ``&&pattern`` and the module was never idempotent for such channels.
- valkey_wait - fail immediately on authentication error instead of retrying until timeout.
- valkey_wait - handle separately info command execute. Using predefined method it could fail even though module should wait.
- valkey_wait - remove KeyError exception in lookup at info response. This could cause early module fail.

v0.5.1
======

Release Summary
---------------

This is bugfix release.

Bugfixes
--------

- valkey_config - properly handle yes/no as value. Ansible silently converts them to bool value so normalize it in module to yes/no.

v0.5.0
======

Release Summary
---------------

This is minor release of the collection.

New Modules
-----------

- valkey_config - Change runtime valkey configs.

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
