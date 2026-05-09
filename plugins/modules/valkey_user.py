# Copyright (c) 2026 Rafał Kozłowski <rafalkozlowski07@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: valkey_user

version_added: "0.1.0"

author:
  - Rafał Kozłowski (@rkozlo)

short_description: Create, update or delete users in valkey

extends_documentation_fragment:
  - rkozlo.valkey.valkey_client_common

description:
  - This module manages users on a Valkey server, allowing you to create, update, or delete users with specific permissions and configurations.
  - The module supports various parameters to define user properties such as passwords, commands, keys,
    channels and categories.
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
      - Commands must be prefixed with I(+) or I(-).
      - Commands works only in append mode.
      - Valkey doesn't has an option to reset commands.If needed you can achieve this togehter with O(categories).
        When passed I(-@all) unlisted commands will be wiped.
        For now workaround needed to acutally revoke if O(categories) not differs.
    type: list
    elements: str
    required: false
  key_patterns:
    description:
      - List of key patters for the user.
      - By default it works in append mode.
      - To save this as state use O(reset_key_patterns).
      - Idempotency for now is flawed. Normally it will be idempotent but when on input redundant patterns it can break it.
        For example passing ['~test:*', '%R~test:*'] %R is redundand and module for now will detect this as changed.
    type: list
    elements: str
    required: false
  channels:
    description:
      - List of channels for the user to append. If want to reset look O(reset_channels).
      - Literal string values are accepted. Do not prefix them with I(&).
      - Notice allchannels here will not be I(&*) like in valkey-server documentation. Result will be I(&allchannels).
    type: list
    elements: str
    required: false
  categories:
    description:
      - List of categories for the user.
      - Categories has to be prefixed with I(-) or I(+).
      - Categories can be passed also without I(@).
      - Module itself doesn't have default value. Valkey for new users will apply I(-@all) if I(+@all) not passed explicity.
      - Order of passed values matters.
      - Option is idempotent only if passed categories makes sense.
      - Option does not touch categories for existing users if not used in module.
      - Option will be working in append mode. If you want to keep it as state best practise is explicity pass I(-@all) as first category.
      - To reset user categories pass I(-@all)
    type: list
    elements: str
  reset_passwords:
    description:
      - Whether overwrite or append passwords.
      - I(true) means existing passwords will be deleted and O(passwords) and O(hashed_passwords) will be added.
      - I(false) means O(passwords) and O(hashed_passwords) will be added to existing passwords.
      - When I(true) still will be idempotent. If existing passwords are exact O(passwords) and O(hashed_passwords)
    type: bool
    default: false
  reset_key_patterns:
    description:
      - Whether overwrite or append key patterns.
      - I(true) means existing key patterns will be deleted and O(key_patterns) will be added.
      - I(false) means O(key_patterns) will be appended to extisitng key patterns.
      - When I(true) still will be idempotent if existing key paterns are equal to O(key_patterns).
    type: bool
    default: false
  reset_channels:
    description:
      - Whether overwrite or append channels.
      - I(true) means existing channels will be deleted and O(channels) will be added.
      - I(false) means O(channels) will be appended to existing channels.
      - When I(true) still will be idempotent if existing channels are equal to O(channels).
    type: bool
    default: false
'''

EXAMPLES = r'''
- name: Create plain user
  rkozlo.valkey.valkey_user:
    name: test_user

- name: Create user with single password in append mode
  rkozlo.valkey.valkey_user:
    name: test_user
    passwords:
      - test_pass

- name: Create plain user with passwords passed as hash and value in append mode
  rkozlo.valkey.valkey_user:
    name: test_user
    passwords:
      - test_pass
    hashed_password:
      - 10a6e6cc8311a3e2bcc09bf6c199adecd5dd59408c343e926b129c4914f3cb01

- name: Create user with passwords in reset mode
  rkozlo.valkey.valkey_user:
    name: test_user
    passwords:
      - test_pass
    reset_passwords: true

- name: Create user with key patterns in append mode
  rkozlo.valkey.valkey_user:
    name: test_user
    key_patterns:
      - "~test:*"
      - "%R~readonly:*"

- name: Create user with key patterns in reset mode
  rkozlo.valkey.valkey_user:
    name: test_user
    key_patterns:
      - "~test:*"
    reset_key_patterns: true

- name: Create user with channels in append mode
  rkozlo.valkey.valkey_user:
    name: test_user
    channels:
      - channel1
      - channel2*

- name: Create user with channels in reset mode
  rkozlo.valkey.valkey_user:
    name: test_user
    channels:
      - channel1
    reset_channels: true

- name: Create user with categories
  rkozlo.valkey.valkey_user:
    name: test_user
    categories:
      - +@connection

- name: Create user with categories
  rkozlo.valkey.valkey_user:
    name: test_user
    categories:
      - -@all
      - +@connection

- name: Create user with commands
  rkozlo.valkey.valkey_user:
    name: test_user
    commands:
      - +get

- name: Create user with commands and categories
  rkozlo.valkey.valkey_user:
    name: test_user
    commands:
      - -get
    categories:
      - -@all
      - +read
'''

RETURN = r'''
---
changed:
  description: Whether the module made changes.
  returned: always
  type: bool
executed_statements:
  description: Operations that were executed or would be executed in check mode.
  returned: on success
  type: list
  elements: dict
  contains:
    action:
      description: Operation type (create_user, update_user, delete_user)
      type: str
      sample: create_user
    params:
      description: Parameters passed to the operation
      type: dict
      sample: {"username": "test_user", "enabled": true}
    args:
      description: Arguments for delete_user operation
      type: list
      sample: ["test_user"]
'''

import hashlib
import re

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey import get_client_common_argument_spec, get_main_conn_kwargs
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
        self._key_patterns = None
        self._channels = None
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
    def key_patterns(self):
        if self._key_patterns is None:
            self._load()
        return self._key_patterns

    @property
    def channels(self):
        if self._channels is None:
            self._load()
        return self._channels

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
        self._key_patterns = result.get('keys', [])
        self._channels = result.get('channels', [])
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

    def _normalize_key_patterns(self, key_patterns):
        '''Key patterns needs to normalize for idempotency.'''
        '''Valkey stores them as upper case so prefixes will be uppered.'''
        '''Possible prefixes:
            %R~  - read
            %W~  - write
            ~    - read/write
            %RW~ - just alias to ~
            %WR~ - as above
            When not explicity passed prefix pattern will be prefixed with ~ just as default for valkey.
        '''
        if not key_patterns:
            return []
        pattern = re.compile(r'^(%RW~|%WR~|%R~|%W~|~)?(.*)$', re.IGNORECASE)
        normalized = []

        for key in key_patterns:
            match = pattern.match(key)
            prefix, rest = match.groups()

            if prefix and prefix.upper() in ('%RW~', '%WR~'):
                normalized.append(f"~{rest}")
            elif prefix:
                normalized.append(f"{prefix.upper()}{rest}")  # Normalize case
            elif key.startswith('%'):
                self.module.fail_json(msg=f'Invalid key prefix: {key}. Example correct prefixes %R~ %RW~ ~')
            else:
                # No prefix passed. Fill with RW
                normalized.append(f"~{key}")

        return normalized

    def _normalize_channels_for_comparison(self, channels):
        """Remove & prefix from channel patterns. Used only to compare."""
        if not channels:
            return []

        normalized = []
        for channel in channels:
            if channel.startswith('&'):
                normalized.append(channel[1:])  # Remove first character
            else:
                normalized.append(channel)
        return normalized

    def _normalize_commands(self, commands):
        if not commands:
            return []
        errors = []
        normalized = []
        available_commands = self._get_available_commands()
        for command in commands:
            if not command.startswith(('+', '-')):
                errors.append(f'Invalid command {command}. Should starts with + or -.')
                continue

            sign = command[0]
            rest = command[1:].lower()

            # Do not allow categories.
            if rest.startswith('@'):
                errors.append(f'Invalid command {command}. For categories use option categories.')

            # Check if command is supported in current version.
            if rest not in available_commands:
                errors.append(f"Invalid command: {command}. Not supported in valkey.")
            normalized.append(sign + rest)

        if errors:
            self.module.fail_json(msg=" | ".join(errors))
        return normalized

    def _get_available_commands(self):
        return self.client._execute("command_list")

    def _commands_needs_update(self, commands):
        if set(commands) == set(self.commands):
            return False

        if set(commands).issubset(set(self.commands)):
            return False
        return True

    def _build_acl_params(self, enabled, passwords, hashed_passwords,
                          commands, key_patterns, channels, categories,
                          reset_passwords=False, reset_key_patterns=False, reset_channels=False):
        params = {
            'username': self.name,
            'enabled': enabled,
            'reset_passwords': reset_passwords,
            'reset_keys': reset_key_patterns,
            'reset_channels': reset_channels
        }
        if passwords:
            params['passwords'] = passwords
        if hashed_passwords:
            params['hashed_passwords'] = hashed_passwords
        if commands:
            params['commands'] = commands
        if key_patterns:
            params['keys'] = key_patterns
        if channels:
            params['channels'] = channels
        if categories:
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

    def _key_patterns_needs_update(self, key_patterns, reset_key_patterns):
        desired_patterns = key_patterns or []
        if set(desired_patterns) == set(self.key_patterns):
            return False
        if not reset_key_patterns:
            if set(desired_patterns).issubset(set(self.key_patterns)):
                return False
        return True

    def _channels_needs_update(self, channels, reset_channels):
        desired_channels = channels or []
        preformated_self_channels = self._normalize_channels_for_comparison(self.channels)
        if set(desired_channels) == set(preformated_self_channels):
            return False
        if not reset_channels:
            if set(desired_channels).issubset(set(preformated_self_channels)):
                return False
        return True

    def _categories_needs_update(self, categories):
        desired = categories or []
        current = set(self.categories)

        # Special case: resetting to default
        if desired == ['-@all']:
            # Need update if current has any categories beyond implicit -@all
            return current != set(['-@all'])

        # Normal case: check if desired is already fully present
        return not set(desired).issubset(current)

    def _normalize_categories(self, categories):
        available_categories = self._get_available_categories()
        if not categories:
            return []
        errors = []
        normalized = []

        for cat_rule in categories:
            # Extract sign and category
            if not cat_rule.startswith(('+', '-')):
                errors.append(f"Invalid category rule '{cat_rule}': must start with + or -")

            # Prereserve sign
            sign = cat_rule[0]
            rest = cat_rule[1:]

            # Remove @. Need for validation.
            if rest.startswith('@'):
                cat_name = rest[1:]
            else:
                cat_name = rest

            # Check if category is supported in current version.
            if cat_name != 'all' and cat_name not in available_categories:
                errors.append(f"Invalid category: {cat_name}")

            # Normalize: sign + '@' + category
            normalized.append(f"{sign}@{cat_name}")
        if errors:
            self.module.fail_json(msg=" | ".join(errors))
        return normalized

    def _get_available_categories(self):
        return self.client._execute('acl_cat')

    def _needs_update(self, enabled, passwords, hashed_passwords, commands, key_patterns, channels,
                      categories, reset_passwords=False, reset_key_patterns=False, reset_channels=False):
        if self.enabled != enabled:
            return True
        if self._passwords_needs_update(passwords, hashed_passwords, reset_passwords):
            return True
        if self._commands_needs_update(commands):
            return True
        if self._key_patterns_needs_update(key_patterns, reset_key_patterns):
            return True
        if self._channels_needs_update(channels, reset_channels):
            return True
        if self._categories_needs_update(categories):
            return True
        return False

    def create(self, enabled=True, passwords=None, hashed_passwords=None, commands=None,
               key_patterns=None, channels=None, categories=None):

        target_passwords, target_hashes = self._extract_passwords(passwords, hashed_passwords)
        categories = self._normalize_categories(categories)
        key_patterns = self._normalize_key_patterns(key_patterns)
        commands = self._normalize_commands(commands)

        params = self._build_acl_params(enabled, target_passwords, target_hashes, commands, key_patterns, channels, categories)
        executed_statements.append({
            'action': 'create_user',
            'params': params
        })
        if not self.module.check_mode:
            self.client._execute('acl_setuser', **params)

        return True

    def update(self, enabled=None, passwords=None, hashed_passwords=None, commands=None,
               key_patterns=None, channels=None, categories=None, reset_passwords=False,
               reset_key_patterns=False, reset_channels=False):

        target_passwords, target_hashes = self._extract_passwords(passwords, hashed_passwords)
        categories = self._normalize_categories(categories)
        key_patterns = self._normalize_key_patterns(key_patterns)
        commands = self._normalize_commands(commands)

        if not self._needs_update(enabled, passwords, hashed_passwords, commands, key_patterns, channels,
                                  categories, reset_passwords, reset_key_patterns, reset_channels):
            return False

        params = self._build_acl_params(enabled, target_passwords, target_hashes, commands, key_patterns,
                                        channels, categories, reset_passwords, reset_key_patterns, reset_channels)

        executed_statements.append({
            'action': 'update_user',
            'params': params
        })
        if not self.module.check_mode:
            self.client._execute('acl_setuser', **params)

        return True

    def delete(self):
        args = [self.name]
        executed_statements.append({
            'action': 'delete_user',
            'args': args
        })
        if not self.module.check_mode:
            self.client._execute('acl_deluser', *args)

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
        key_patterns=dict(type='list', elements='str', required=False, default=None, no_log=False),
        channels=dict(type='list', elements='str', required=False, default=None),
        categories=dict(type='list', elements='str'),
        reset_passwords=dict(type='bool', default=False),
        reset_key_patterns=dict(type='bool', default=False),
        reset_channels=dict(type='bool', default=False)
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
    hashed_passwords = module.params['hashed_passwords']
    commands = module.params['commands']
    key_patterns = module.params['key_patterns']
    channels = module.params['channels']
    categories = module.params['categories']
    reset_passwords = module.params['reset_passwords']
    reset_key_patterns = module.params['reset_key_patterns']
    reset_channels = module.params['reset_channels']

    valkey_user = ValkeyUser(module, client, name=name)
    changed = False
    if state == 'present':
        if not valkey_user.exists:
            changed = valkey_user.create(enabled=enabled, passwords=passwords, hashed_passwords=hashed_passwords, commands=commands,
                                         key_patterns=key_patterns, channels=channels, categories=categories)
        else:
            changed = valkey_user.update(enabled=enabled, passwords=passwords, hashed_passwords=hashed_passwords, commands=commands,
                                         key_patterns=key_patterns, channels=channels, categories=categories, reset_passwords=reset_passwords,
                                         reset_channels=reset_channels, reset_key_patterns=reset_key_patterns)
    else:
        if valkey_user.exists:
            changed = valkey_user.delete()

    module.exit_json(changed=changed, executed_statements=executed_statements)


if __name__ == '__main__':
    main()
