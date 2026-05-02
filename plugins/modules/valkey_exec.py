# Copyright (c) 2026 Rafał Kozłowski <rafalkozlowski07@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
'''

EXAMPLES = r'''

'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey import get_client_common_argument_spec, get_main_conn_kwargs
from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey_client import ValkeyClient

executed_statements = []

class ValkeyExec:
    def __init__(self, module, client, command, params):
        self.module = module
        self.client = client
        self.command = command.lower()
        self.params = params

    def execute(self):
        executed_statements.append(
            {'command': self.command, 'params': self.params}
        )
        if not self.module.check_mode:
            result = self.client._execute(self.command, **self.params)

        return result or []


def main():
    argument_spec = get_client_common_argument_spec()
    argument_spec.update(
        command=dict(type='str', required=True),
        params=dict(type='dict')
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    conn_kwargs = get_main_conn_kwargs(module)
    client_kwargs = module.params.get('client_kwargs', {})
    conn_kwargs.update(client_kwargs)
    client = ValkeyClient(module, **conn_kwargs)

    command = module.params['command']
    params = module.params['params']

    valkey_raw_command = ValkeyExec(module, client, command, params)

    result = valkey_raw_command.execute()

    module.exit_json(changed=True, result=result, executed_statements=executed_statements)

if __name__ == '__main__':
    main()
