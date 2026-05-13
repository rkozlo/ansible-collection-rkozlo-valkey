from __future__ import absolute_import, division, print_function

__metaclass__ = type


def get_client_common_argument_spec():
    return dict(
        login_host=dict(type='str', default='localhost'),
        login_port=dict(type='int', default=6379),
        login_db=dict(type='int', required=False),
        login_user=dict(type='str', default='default'),
        cluster=dict(type='bool', default=False),
        login_password=dict(type='str', default=None, no_log=True),
        client_kwargs=dict(type='dict', default={}),
    )


def get_main_conn_kwargs(module):
    main_conn_kwargs = {}
    main_conn_kwargs['host'] = module.params['login_host']  # Has a default value
    if module.params['login_port']:
        main_conn_kwargs['port'] = module.params['login_port']
    if module.params['login_db']:
        main_conn_kwargs['db'] = module.params['login_db']
    if module.params['login_user']:
        main_conn_kwargs['username'] = module.params['login_user']
    if module.params['login_password']:
        main_conn_kwargs['password'] = module.params['login_password']

    return main_conn_kwargs


# Some outputs like cluster_slots will be broken without serialization
def _make_serializable(obj):
    """Convert non-JSON-serializable objects to serializable form."""
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            # Convert tuple keys to string representation
            if isinstance(k, tuple):
                k = str(k)
            new_dict[k] = _make_serializable(v)
        return new_dict
    elif isinstance(obj, tuple):
        # Convert tuple values to list (JSON supports lists, not tuples)
        return [_make_serializable(item) for item in obj]
    elif isinstance(obj, list):
        return [_make_serializable(item) for item in obj]
    else:
        return obj
