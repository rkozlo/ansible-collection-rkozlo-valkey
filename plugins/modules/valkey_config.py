# Copyright (c) 2026 Rafał Kozłowski <rafalkozlowski07@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: valkey_config

version_added: "0.5.0"

author:
  - Rafał Kozłowski (@rkozlo)
short_description: Change runtime valkey configs.
extends_documentation_fragment:
  - rkozlo.valkey.valkey_client_common
description:
  - This module allows you to change valkey configs.
  - Module will try change configs only if differs.
  - Module knows what settings are immutable and will not try to change them
    generating errors in server.
attributes:
  check_mode:
    description: Supports check_mode.
    support: full
  diff_mode:
    description: Returns before and after values of changed configs.
    support: full
  idempotent:
    description: When run twice in a row outside check mode, with the same arguments, the second invocation indicates no change.
    support: partial
    details: Only when values are passed in the form described in O(configs).
options:
  configs:
    description:
      - Config dictionary module will ensure has proper value set.
      - Values are compared with the current value returned by C(CONFIG GET) as strings.
      - Only limited normalization is done before comparing.
      - Sizes like V(100mb) or V(1G) are converted to bytes. C(K), C(M), C(G) are multiples of 1000
        and C(KB), C(MB), C(GB) are multiples of 1024, same as in Valkey. Units are case insensitive.
      - Booleans are converted to V(yes) and V(no).
      - Any other value is compared exactly. To stay idempotent pass it in the same form C(CONFIG GET) returns,
        for example lowercase V(allkeys-lru), or V(slave) instead of V(replica) in C(client-output-buffer-limit).
    required: true
    type: dict
  strict:
    description:
      - How module should handle immutable attributes.
      - When C(false) immutable attributes will be logged in return and only proper warning appears.
      - When C(true) config that is immutable and can't be changed during runtime module will fail.
      - In strict mode module will fail early if any immutable config was set. Without changing anything.
    type: bool
    default: false
  config_rewrite:
    description:
      - Whether module will execute V(CONFIG REWRITE) or not.
      - Module will rewrite only if runtime configs differ.
      - Module does not detect inconsistency between config file and runtime values.
        If they already differ before running the module, no rewrite is done.
    type: bool
    default: false
'''
EXAMPLES = r'''
- name: Change one config
  rkozlo.valkey.valkey_config:
    configs:
      maxmemory: 100000

- name: Change many configs
  rkozlo.valkey.valkey_config:
    configs:
      maxmemory: 100000
      save: 60 60
      client-output-buffer-limit: "normal 1 1 1 slave 268435456 67108864 60 pubsub 33554432 8388608 60"

- name: Trying change immutable config - successful with warning
  rkozlo.valkey.valkey_config:
    configs:
      logfile: new_file

- name: Trying change immutable config in strict - ends with error
  rkozlo.valkey.valkey_config:
    configs:
      logfile: new_file
    strict: true

- name: Change config and execute config rewrite on change
  rkozlo.valkey.valkey_config:
    configs:
      maxmemory: 100000
    config_rewrite: true
'''
RETURN = r'''
immutable:
  description: List of changes that differ but can't be applied.
  type: list
  elements: dict
  returned: on success
  contains:
    after:
      description: Value after change.
      type: str
    before:
      description: Value before change.
      type: str
    name:
      description: Name of changed config.
      type: str
  sample:
    - after: "new_file"
      before: ""
      name: logfile
changed_configs:
  description:
    - List of configs that differed and were applied.
    - Before version 0.6.0 it was returned as C(diff) which collided with Ansible diff mode.
  type: list
  elements: dict
  returned: on success
  contains:
    after:
      description: Value after change.
      type: str
    before:
      description: Value before change.
      type: str
    name:
      description: Name of changed config.
      type: str
  sample:
    - after: "100000"
      before: "0"
      name: "maxmemory"
  version_added: 0.6.0
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey import (
    get_client_common_argument_spec, get_main_conn_kwargs,
    to_bytes_data,
    POSSIBLE_SIZE_PATTERN,
)
from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey_client import ValkeyClient


class ValkeyConfig:
    def __init__(self, module, client, strict, config_rewrite, configs=None):
        self.module = module
        self.client = client
        self.strict = strict
        self.config_rewrite = config_rewrite
        self.configs_to_change = configs
        self._config = None
        self._version_config = None

    @property
    def config(self):
        if self._config is None:
            self.fetch()
        return self._config

    @property
    def version_config(self):
        if self._version_config is None:
            self._load_configs()
        return self._version_config

    def fetch(self):
        if self.configs_to_change is None:
            args = '*'
        else:
            args = self.configs_to_change.keys()
        self._config = self.client._execute('config_get', *args)

    def _load_configs(self):
        """Load configs for used server version."""
        from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey_config_ver import CONFIGS
        version_key = f'{self.client.version["major"]}.{self.client.version["minor"]}'
        try:
            self._version_config = CONFIGS[version_key]
        except KeyError:
            self.module.fail_json(msg=f"Valkey {version_key} is not supported yet. Supported: {', '.join(CONFIGS)}")

    def get_diff_runtime_configs(self, configs):
        different = {}
        for config, value in configs.items():
            normalized = self.normalize_value(value)
            try:
                current = self.config[config]
            except KeyError:
                self.module.fail_json(msg=f'Config {config} is not known by this Valkey server.')
            if str(normalized) != str(current):
                different[config] = normalized
        return different

    def is_immutable_attr(self, name):
        try:
            return self.version_config[name]['immutable']
        except KeyError:
            self.module.fail_json(msg=f"Config {name} is not known for Valkey {self.client.version['full']}.")

    def extract_immutable_attributes(self, configs):
        immutable = {}
        final = {}
        for config, value in configs.items():
            if self.is_immutable_attr(config) is True:
                immutable[config] = value
                continue
            final[config] = value
        return final, immutable

    def set_configs(self, configs):
        self.validate_passed_params()
        diff_configs = self.get_diff_runtime_configs(configs)
        changed = False
        changed_configs = []
        cant_change = []
        if not diff_configs:
            return changed, changed_configs, cant_change
        to_change_configs, immutable = self.extract_immutable_attributes(diff_configs)

        if immutable:
            if self.strict:
                self.module.fail_json(msg=f"Configs differ but can't be changed because they are immutable: {immutable}")
            else:
                self.module.warn(f'''configs: {immutable} are immutable and can't be changed during runtime.''')
        if to_change_configs:
            changed = True
            args = [
                str(item)
                for config, value in to_change_configs.items()
                for item in (config, value)
            ]
            if not self.module.check_mode:
                self.client._execute('config_set', *args)
                if self.config_rewrite:
                    self.client._execute('config_rewrite')
            for config, value in to_change_configs.items():
                changed_configs.append(self.build_to_string(config, value))

        for config, value in immutable.items():
            cant_change.append(self.build_to_string(config, value))

        return changed, changed_configs, cant_change

    def build_diff(self, changed_configs):
        return {
            'before': {c['name']: c['before'] for c in changed_configs},
            'after': {c['name']: c['after'] for c in changed_configs},
        }

    def build_to_string(self, setting, value):
        return {
            'name': setting,
            'before': self.config[setting],
            'after': str(value),
        }

    def normalize_value(self, value):
        if POSSIBLE_SIZE_PATTERN.match(str(value)):
            return to_bytes_data(str(value))
        # Ansible translate yes/no to bool True/False so explicity handle this.
        elif value is False:
            return "no"
        elif value is True:
            return "yes"
        return str(value)

    def validate_passed_params(self):
        if self.config_rewrite and not self.client.config_rewrite_supported:
            self.module.fail_json(msg='Config rewrite passed but not supported on this instance. Config file is not defined.')


def main():
    argument_spec = get_client_common_argument_spec()
    argument_spec.update(
        configs=dict(type='dict', required=True),
        strict=dict(type='bool', default=False),
        config_rewrite=dict(type='bool', default=False)
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    conn_kwargs = get_main_conn_kwargs(module)
    client_kwargs = module.params.get('client_kwargs', {})
    conn_kwargs.update(client_kwargs)
    cluster = module.params['cluster']
    configs = module.params['configs']
    strict = module.params['strict']
    config_rewrite = module.params['config_rewrite']

    client = ValkeyClient(module, cluster, **conn_kwargs)

    valkey_config = ValkeyConfig(module, client, strict, config_rewrite, configs)

    changed, changed_configs, immutable = valkey_config.set_configs(configs)
    result = dict(changed=changed, changed_configs=changed_configs, immutable=immutable)
    if module._diff:
        result['diff'] = valkey_config.build_diff(changed_configs)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
