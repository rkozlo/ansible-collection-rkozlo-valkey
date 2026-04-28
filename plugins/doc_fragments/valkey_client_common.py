from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
options:
  login_host:
    description: Hostname or IP address of the Valkey server
    type: str
    default: localhost
  login_port:
    description: Port number of the Valkey server
    type: int
    default: 6379
  login_db:
    description: Database number
    type: int
    default: 0
  login_user:
    description: Username for authentication
    type: str
    default: default
  login_password:
    description: Password for authentication
    type: str
  client_kwargs:
    description: Additional keyword arguments to pass to the Valkey client
    type: dict
    default: {}

requirements:
  - valkey
'''
