from __future__ import absolute_import, division, print_function

__metaclass__ = type


def get_client_common_argument_spec():
    return dict(
        login_host=dict(type='str', default='localhost'),
        login_port=dict(type='int', default=6379),
        login_db=dict(type='int', default=0),
        login_user=dict(type='str', default='default'),
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


def format_params_to_string(input):
    return ' '.join([f"{k}={v}" for k, v in input.items()])
