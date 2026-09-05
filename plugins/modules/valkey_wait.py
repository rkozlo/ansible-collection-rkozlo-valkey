# Copyright (c) 2026 Rafał Kozłowski <rafalkozlowski07@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: valkey_wait

version_added: "0.4.0"

author:
  - Rafał Kozłowski (@rkozlo)

short_description: Wait until Valkey will be in certain condition.

extends_documentation_fragment:
  - rkozlo.valkey.valkey_client_common

description:
  - This module waits until valkey be in desired state.
  - Can be used as orchestrator for example waiting until RDB is loading
    AOF is rewriting, replica is still syncing, valkey is not ready to accept connections.

options:
  state:
    description:
      - Desired state of Valkey.
      - In this moment it accepts only I(ready).
      - Will check if valkey response is reachable, passed authentication working and responding to ping.
    type: str
    choices: ['ready']
    required: false
  interval:
    description:
      - Interval between checks in second.
    type: int
    default: 1
  timeout:
    description:
      - How many tries until decides to fail.
      - Duration related with O(interval).
    type: int
    default: 60
  conditions:
    description:
      - Conditions module will observe if are met.
      - >
        You can use any field described in INFO ex. [ {role: slave} ].
    type: dict
    required: false
'''

EXAMPLES = r'''
- name: Wait for server to start
  rkozlo.valkey.valkey_wait:
    state: ready

- name: Wait for server to start changing intervals
  rkozlo.valkey.valkey_wait:
    state: ready
    interval: 5
    timeout: 10
'''

RETURN = r'''
---
changed:
  description: Whether the module made changes.
  returned: always
  type: bool
info:
  description: Statistics about wait status.
  returned: always
  type: dict
  sample: [{
        "state": {
            "current_retry": 1,
            "expected": "ready",
            "fail_retries": 0,
            "is_met": true,
            "last_check_time": null,
            "last_value": true
        }
    }]
fail_waits:
  description: Statistics about failed waits.
  returned: on failure
  type: dict
  sample: [{
        "state": {
            "current_retry": 5,
            "expected": "ready",
            "fail_retries": 0,
            "is_met": false,
            "last_check_time": null,
            "last_value": false
        }
    }]
'''


from time import sleep
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native
from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey import get_client_common_argument_spec, get_main_conn_kwargs
from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey_client import ValkeyClient

try:
    import valkey.exceptions
    HAS_VALKEY_PACKAGE = True
except ImportError:
    HAS_VALKEY_PACKAGE = False
    Valkey = None
    valkey_exceptions = None


class ValkeyWait:
    def __init__(self, module, client):
        self.module = module
        self.client = client
        self.interval = module.params['interval']
        self.timeout = module.params['timeout']
        self.state = module.params['state']
        self.conditions = module.params['conditions']
        self._retry = 0
        self.statistics = self._initialize_statistics()

    def _initialize_statistics(self):
        statistics = {}
        base_info = {
            'fail_retries': 0,
            'last_value': 'down',
            'current_retry': 0,
            'last_check_time': None,
            'is_met': False
        }
        if self.state:
            statistics['state'] = {
                **base_info,
                'expected': self.state,
            }
        if self.conditions:
            for condition, val in self.conditions.items():
                statistics[condition] = {
                    **base_info,
                    'expected': val,
                }
        return statistics

    def _fetch_info(self):
        return self.client._execute('info')

    def _wait_for_state(self):
        try:
            self.client.client.ping()
        except valkey.exceptions.ConnectionError:
            return 'down'
        except valkey.exceptions.ResponseError:
            return 'down'
        except Exception as e:
            self.module.fail_json(msg="Unexpected exception: %s" % to_native(e))
        return 'ready'

    def run(self):
        while self._retry < self.timeout:
            if not self.statistics['state']['is_met']:
                return_state = self._wait_for_state()
                self.statistics['state']['is_met'] = True if return_state == self.statistics['state']['expected'] else False
                self.statistics['state']['last_value'] = return_state
                self.statistics['state']['current_retry'] += 1
                self._retry += 1
                if self.statistics['state']['is_met']:
                    return True
            sleep(self.interval)
        return False

    def return_summary(self):
        return self.statistics

    def return_failed(self):
        return {k: v for k, v in self.statistics.items() if not v.get('is_met')}


def main():
    argument_spec = get_client_common_argument_spec()
    argument_spec.update(
        interval=dict(type='int', default=1),
        timeout=dict(type='int', default=60),
        state=dict(type='str', required=False, choices=['ready']),
        conditions=dict(type='dict', required=False)
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    conn_kwargs = get_main_conn_kwargs(module)
    client_kwargs = module.params.get('client_kwargs', {})
    conn_kwargs.update(client_kwargs)
    cluster = module.params['cluster']

    client = ValkeyClient(module, cluster, **conn_kwargs)

    valkey_wait = ValkeyWait(module, client)
    result = valkey_wait.run()
    if result:
        module.exit_json(changed=False, info=valkey_wait.return_summary())
    else:
        module.fail_json(msg="Failed", info=valkey_wait.return_summary(), fail_waits=valkey_wait.return_failed())


if __name__ == '__main__':
    main()
