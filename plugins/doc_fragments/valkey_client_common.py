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
  cluster:
    description: Wheter connect in cluster mode or not. Currently only passing one host is supported.
    type: bool
    default: false
    version_added: 0.3.0

requirements:
  - valkey
'''
