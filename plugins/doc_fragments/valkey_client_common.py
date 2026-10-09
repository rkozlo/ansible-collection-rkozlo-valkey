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
    description:
      - Database number.
      - Not supported together with O(cluster=true). Valkey cluster uses only database 0 at this moment.
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
    description:
      - Whether to connect in cluster mode or not.
      - Only one node can be passed with O(login_host) and O(login_port). Other nodes are discovered from it.
      - Server commands used by modules like C(CONFIG GET), C(CONFIG SET), C(CONFIG REWRITE), C(ACL SETUSER),
        C(ACL SAVE) and C(INFO) are not sent to all nodes. They are executed only on a single node of the cluster,
        which is not always the one passed in O(login_host).
      - To manage configs or users on every node, connect to each node separately with O(cluster=false).
    type: bool
    default: false
    version_added: 0.3.0

requirements:
  - valkey
'''
