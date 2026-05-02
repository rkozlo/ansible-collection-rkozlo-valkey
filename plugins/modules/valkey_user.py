# Copyright (c) 2026 Rafał Kozłowski <rafalkozlowski07@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: valkey_user

version_added: "0.0.1"

author:
  - Rafał Kozłowski (@rkozlo)

short_description: Create, update or delete users in valkey

extends_documentation_fragment:
  - rkozlo.valkey.valkey_client_common

description:
  - This module manages users on a Valkey server, allowing you to create, update, or delete users with specific permissions and configurations.
  - The module supports various parameters to define user properties such as passwords, commands, keys,
    channels, selectors, and categories.
  - It also supports appending new passwords, keys, or channels to existing ones without overwriting them.

options:
  name:
    description:
      - The name of the user to manage.
    type: str
    required: true
  enabled:
    description:
      - Whether the user should be enabled or disabled.
    type: bool
    default: true
  state:
    description:
      - Desired state of the user.
    type: str
    default: present
    choices: ['present', 'absent']
  passwords:
    description:
      - List of plaintext passwords for the user.
    type: list
    elements: str
    required: false
  hashed_passwords:
    description:
      - List of hashed passwords for the user.
    type: list
    elements: str
    required: false
  commands:
    description:
      - List of commands for the user.
    type: list
    elements: str
    required: false
  keys:
    description:
      - List of keys for the user.
    type: list
    elements: str
    required: false
  channels:
    description:
      - List of channels for the user.
    type: list
    elements: str
    required: false
  selectors:
    description:
      - List of selectors for the user.
    type: list
    elements: str
    required: false
  categories:
    description:
      - List of categories for the user.
    type: list
    elements: str
    required: false
  reset_passwords:
    description:
      - Whetere overwrite or append passwords.
    type: bool
    default: false
  reset_keys:
    description:
      - Whetere overwrite or append keys.
    type: bool
    default: false
  reset_channels:
    description:
      - Whetere overwrite or append channels.
    type: bool
    default: false
'''

EXAMPLES = r'''

'''

RETURN = r'''
'''


import hashlib

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey import get_client_common_argument_spec, get_main_conn_kwargs, format_params_to_string
from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey_client import ValkeyClient

executed_statements = []


class ValkeyUser:
    def __init__(self, module, client, name):
        self.module = module
        self.client = client
        self.name = name
        self._exists = None
        self._passwords = None
        self._commands = None
        self._keys = None
        self._channels = None
        self._selectors = None
        self._categories = None
        self._enabled = None

    @property
    def exists(self):
        if self._exists is None:
            self._load()
        return self._exists

    @property
    def passwords(self):
        if self._passwords is None:
            self._load()
        return self._passwords

    @property
    def commands(self):
        if self._commands is None:
            self._load()
        return self._commands

    @property
    def keys(self):
        if self._keys is None:
            self._load()
        return self._keys

    @property
    def channels(self):
        if self._channels is None:
            self._load()
        return self._channels

    @property
    def selectors(self):
        if self._selectors is None:
            self._load()
        return self._selectors

    @property
    def categories(self):
        if self._categories is None:
            self._load()
        return self._categories

    @property
    def enabled(self):
        if self._enabled is None:
            self._load()
        return self._enabled

    def _load(self):
        if self._exists is not None:
            return

        result = self.client._execute('acl_getuser', username=self.name)

        if not result:
            self._exists = False
            return
        self._exists = True
        self._passwords = result.get('passwords', [])
        self._commands = result.get('commands', [])
        self._keys = result.get('keys', [])
        self._channels = result.get('channels', [])
        self._selectors = result.get('selectors', [])
        self._categories = result.get('categories', [])
        self._enabled = result.get('enabled')

    def _extract_passwords(self, passwords, hashed_passwords):
        target_passwords = []
        target_hashes = []
        for _entry in (passwords or []):
            target_passwords.append('+' + _entry)
        for _entry in (hashed_passwords or []):
            target_hashes.append('+' + _entry)
        return target_passwords, target_hashes

    def _normalize_passwords_and_hashes(self, passwords, hashed_passwords):
        result = []
        if hashed_passwords:
            result += hashed_passwords
        if passwords:
            for password in passwords:
                if password not in result:
                    result.append(hashlib.sha256(password.encode('utf-8')).hexdigest())
        return result

    def _build_acl_params(self, username, enabled, passwords, hashed_passwords,
                          commands, keys, channels, selectors, categories,
                          reset_passwords=False, reset_keys=False, reset_channels=False):
        params = {
            'username': username,
            'enabled': enabled,
            'passwords': passwords,
            'hashed_passwords': hashed_passwords,
            'reset_passwords': False,
            'reset_keys': False,
            'reset_channels': False
        }
        if commands is not None:
            params['commands'] = commands
        if keys is not None:
            params['keys'] = keys
        if channels is not None:
            params['channels'] = channels
        if selectors is not None:
            params['selectors'] = selectors
        if categories is not None:
            params['categories'] = categories
        return params

    def _compare_passwords(self, desired):
        return set(desired) == set(self.passwords)

    def _passwords_needs_update(self, passwords, hashed_passwords, reset_passwords):
        normalized_hashes = self._normalize_passwords_and_hashes(passwords, hashed_passwords)
        if self._compare_passwords(normalized_hashes):
            return False
        if not reset_passwords:
            if set(normalized_hashes).issubset(set(self.passwords)):
                return False
        return True

    def _keys_needs_update(self, keys, reset_keys):
        desired_keys = keys or []
        if set(desired_keys) == set(self.keys):
            return False
        if not reset_keys:
            if set(desired_keys).issubset(set(self.keys)):
                return False
        return True

    def _channels_needs_update(self, channels, reset_channels):
        desired_channels = channels or []
        if set(desired_channels) == set(self.channels):
            return False
        if not reset_channels:
            if set(desired_channels).issubset(set(self.channels)):
                return False
        return True

    def _categories_needs_update(self, commands=[]):
        '''Commands currently only works in append mode.'''
        '''Idempotency we mean passed commands are part of current command.'''
        '''Also by default -@all is applied to empty new users.'''

        desired_commands = commands or []
        if set(desired_commands).issubset(set(self.commands)):
            return False
        return True
    
    def _normalize_categories(self, categories=[]):
        if not categories or all('@all' not in c for c in categories):
            categories.insert(0, '-@all')
        return categories

    def _needs_update(self, enabled, passwords, hashed_passwords, commands, keys, channels,
                      selectors, categories, reset_passwords=False, reset_keys=False, reset_channels=False):
        if self.enabled != enabled:
            return True
        if self._passwords_needs_update(passwords, hashed_passwords, reset_passwords):
            return True
        if set(self.commands) != set(commands):
            return True
        if self._keys_needs_update(keys, reset_keys):
            return True
        if self._channels_needs_update(channels, reset_channels):
            return True
        desired_selectors = selectors or []
        if set(self.selectors) != set(desired_selectors):
            return True
        if self._categories_needs_update(categories):
            return True
        return False

    def create(self, enabled=True, passwords=None, hashed_passwords=None, commands=None,
               keys=None, channels=None, selectors=None, categories=[]):
        target_passwords, target_hashes = self._extract_passwords(passwords, hashed_passwords)
        categories = self._normalize_categories(categories)
        params = self._build_acl_params(self.name, enabled, target_passwords, target_hashes, commands, keys,channels, selectors, categories)
        executed_statements.append(f"Creating user '{self.name}' with params {format_params_to_string(params)}")
        if not self.module.check_mode:
            self.client._execute('acl_setuser', **params)

        return True

    def update(self, enabled=None, passwords=None, hashed_passwords=None, commands=None,
               keys=None, channels=None, selectors=None, categories=[], reset_passwords=False,
               reset_keys=False, reset_channels=False):
        categories = self._normalize_categories(categories)
        if not self._needs_update(enabled, passwords, hashed_passwords, commands,
                              keys, channels, selectors, categories, reset_passwords,
                              reset_keys, reset_channels):
            return False

        target_passwords, target_hashes = self._extract_passwords(passwords, hashed_passwords)

        params = self._build_acl_params(self.name, enabled, target_passwords, target_hashes,commands, keys,
                                        channels, selectors, categories, reset_channels, reset_keys, reset_channels)

        executed_statements.append(f"Updating user '{self.name}' with params {format_params_to_string(params)}")
        if not self.module.check_mode:
            self.client._execute('acl_setuser', **params)

        return True

    def delete(self):
        executed_statements.append(f"Deleting user '{self.name}'.")
        if not self.module.check_mode:
            self.client._execute('acl_deluser', self.name)

        return True


def main():
    argument_spec = get_client_common_argument_spec()
    argument_spec.update(
        name=dict(type='str', required=True),
        enabled=dict(type='bool', default=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        passwords=dict(type='list', elements='str', required=False, default=None, no_log=True),
        hashed_passwords=dict(type='list', elements='str', required=False, default=None, no_log=True),
        commands=dict(type='list', elements='str', required=False, default=None),
        keys=dict(type='list', elements='str', required=False, default=None, no_log=False),
        channels=dict(type='list', elements='str', required=False, default=None),
        selectors=dict(type='list', elements='str', required=False, default=None),
        categories=dict(type='list', elements='str', default=['-@all']),
        reset_passwords=dict(type='bool', default=False),
        reset_keys=dict(type='bool', default=False),
        reset_channels=dict(type='bool', default=False),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    conn_kwargs = get_main_conn_kwargs(module)
    client_kwargs = module.params.get('client_kwargs', {})
    conn_kwargs.update(client_kwargs)
    client = ValkeyClient(module, **conn_kwargs)

    name = module.params['name']
    enabled = module.params['enabled']
    state = module.params['state']
    passwords = module.params['passwords']
    commands = module.params['commands']
    keys = module.params['keys']
    channels = module.params['channels']
    selectors = module.params['selectors']
    categories = module.params['categories']
    reset_passwords = module.params['reset_passwords']
    reset_keys = module.params['reset_keys']
    reset_channels = module.params['reset_channels']

    valkey_user = ValkeyUser(module, client, name=name)
    changed = False
    if state == 'present':
        if not valkey_user.exists:
            changed = valkey_user.create(enabled=enabled, passwords=passwords, commands=commands, keys=keys,
                                         channels=channels, selectors=selectors, categories=categories)
        else:
            changed = valkey_user.update(enabled=enabled, passwords=passwords, commands=commands, keys=keys,
                                         channels=channels, selectors=selectors, categories=categories,
                                         reset_channels=reset_channels, reset_passwords=reset_passwords,
                                         reset_keys=reset_keys)
    else:
        if valkey_user.exists:
            changed = valkey_user.delete()

    module.exit_json(changed=changed, executed_statements=executed_statements)


if __name__ == '__main__':
    main()
