# Copyright (c) 2026 Rafał Kozłowski <rafalkozlowski07@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: valkey_info

version_added: "0.0.1"

author:
  - Rafał Kozłowski (@rkozlo)

short_description: Gather information about Valkey server

extends_documentation_fragment:
  - rkozlo.valkey.valkey_client_common

description:
  - This module connects to a Valkey server and retrieves information about its configuration, status, and other details.
  - The module supports retrieving specific sections of information based on the provided parameters.
  - Possible sections can be found L(info,https://valkey.io/commands/info/).

options:
  sections:
    description:
      - List of sections to retrieve.
      - Valid sections depend on Valkey version.
      - If not provided, all available information will be retrieved.
    type: list
    elements: str
    required: false
    default: null
'''

EXAMPLES = r'''
- name: Get all Valkey server info
  rkozlo.valkey.valkey_info:
    login_host: localhost
    login_port: 6379
  register: valkey_info

- name: Get specific sections
  rkozlo.valkey.valkey_info:
    login_host: localhost
    login_port: 6379
    sections:
      - server
      - memory
  register: valkey_info

- name: Get info with authentication
  rkozlo.valkey.valkey_info:
    login_host: localhost
    login_port: 6379
    login_user: myuser
    login_password: mypassword
    sections:
      - server
  register: valkey_info
'''

RETURN = r'''
info:
  description: Dictionary containing the Valkey server information
  type: dict
  returned: always
  example:
    valkey_version: "9.0.0"
    valkey_mode: "standalone"
    process_id: 1234
    uptime_in_seconds: 3600
    connected_clients: 10
    used_memory: 1024000
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey import get_client_common_argument_spec, get_main_conn_kwargs
from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey_client import ValkeyClient


class ValkeyInfoModule:
    def __init__(self, module, client, sections=None):
        self.module = module
        self.client = client
        self.sections = sections

    def run(self):
        args = self.sections if self.sections else []
        info = self.client._execute('info', *args)
        return info


def main():
    argument_spec = get_client_common_argument_spec()
    argument_spec.update(
        sections=dict(type='list', elements='str', required=False, default=None)
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    conn_kwargs = get_main_conn_kwargs(module)
    client_kwargs = module.params.get('client_kwargs', {})
    conn_kwargs.update(client_kwargs)
    client = ValkeyClient(module, **conn_kwargs)

    sections = module.params['sections']
    valkey_info_module = ValkeyInfoModule(module, client, sections=sections)
    result = valkey_info_module.run()
    module.exit_json(changed=False, info=result)


if __name__ == '__main__':
    main()
