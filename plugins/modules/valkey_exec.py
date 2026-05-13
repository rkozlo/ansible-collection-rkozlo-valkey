# Copyright (c) 2026 Rafał Kozłowski <rafalkozlowski07@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: valkey_exec

version_added: "0.1.0"

author:
  - Rafał Kozłowski (@rkozlo)
short_description: Execute arbitrary Valkey commands
extends_documentation_fragment:
  - rkozlo.valkey.valkey_client_common
description:
  - This module allows you to execute any Valkey command with specified parameters.
  - It is designed for advanced users who need to perform operations that are not covered by other specific Valkey modules.
  - Use this module with caution, as executing arbitrary commands can lead to unintended consequences if not used properly.
  - Notice that this module will call library method directly.
  - Parameters should be provided in the format expected by the library.
  - For command syntax, see https://valkey-py.readthedocs.io/en/latest/commands.html.

options:
  command:
    description:
      - The Valkey command to execute. This should be a string representing the command, such as C(GET), C(SET), C(HGETALL), etc.
    required: true
    type: str
  args:
    description:
      - A list of positional arguments to pass to the Valkey command.
    required: false
    type: list
    elements: raw
  params:
    description:
      - A dictionary of keyword parameters to pass to the Valkey command.
      - The keys and values should be formatted according to the requirements of the specific command being executed.
      - 'For example, for a C(GET) command, you might provide C({"key": "mykey"}) as the parameters.'
    required: false
    type: dict
'''

EXAMPLES = r'''
- name: Execute GET command with positional args
  rkozlo.valkey.valkey_exec:
    login_host: localhost
    login_port: 6379
    command: GET
    args:
      - mykey
  register: valkey_exec_result

- name: Execute HSET command with keyword params
  rkozlo.valkey.valkey_exec:
    login_host: localhost
    login_port: 6379
    command: HSET
    params:
      name: myhash
      key: field1
      value: value1
  register: valkey_exec_result

- name: Execute command with both args and params
  rkozlo.valkey.valkey_exec:
    login_host: localhost
    login_port: 6379
    command: ZADD
    args:
      - myzset
      - 1
      - member1
    params:
      nx: true
  register: valkey_exec_result
'''

RETURN = r'''
result:
  description: Raw response returned by the executed Valkey command.
  type: raw
  returned: always
  example: "value1"
executed_statements:
  description: A list of executed commands with provided positional and keyword arguments.
  type: list
  returned: always
  elements: dict
  example:
    - command: get
      args:
        - mykey
      params: {}
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey import get_client_common_argument_spec, get_main_conn_kwargs, _make_serializable
from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey_client import ValkeyClient

executed_statements = []


class ValkeyExec:
    def __init__(self, module, client, command, args, params):
        self.module = module
        self.client = client
        self.command = command.lower()
        self.args = args or []
        self.params = params or {}

    def execute(self):
        executed_statements.append(
            {'command': self.command, 'args': self.args, 'params': self.params}
        )
        result = []
        if not self.module.check_mode:
            result = self.client._execute(self.command, *self.args, **self.params)

        return [] if result is None else result


def main():
    argument_spec = get_client_common_argument_spec()
    argument_spec.update(
        command=dict(type='str', required=True),
        args=dict(type='list', elements='raw'),
        params=dict(type='dict')
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    conn_kwargs = get_main_conn_kwargs(module)
    client_kwargs = module.params.get('client_kwargs', {})
    conn_kwargs.update(client_kwargs)
    cluster = module.params['cluster']

    client = ValkeyClient(module, cluster, **conn_kwargs)

    command = module.params['command']
    args = module.params.get('args', [])
    params = module.params.get('params', {})

    valkey_raw_command = ValkeyExec(module, client, command, args, params)

    result = valkey_raw_command.execute()
    result = _make_serializable(result)
    module.exit_json(changed=True, result=result, executed_statements=executed_statements)


if __name__ == '__main__':
    main()
