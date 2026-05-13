from ansible.module_utils.common.text.converters import to_native

try:
    from valkey import Valkey
    from valkey.cluster import ValkeyCluster
    import valkey.exceptions
    HAS_VALKEY_PACKAGE = True
except ImportError:
    HAS_VALKEY_PACKAGE = False
    Valkey = None
    valkey_exceptions = None


class ValkeyClient:
    def __init__(self, module=None, cluster=False, host='localhost', port=6379, username='default', password=None, **client_kwargs):
        if not HAS_VALKEY_PACKAGE:
            module.fail_json(msg="valkey Python package is required. Install with: pip install valkey")
        self.module = module
        self.login_host = host
        self.login_port = port
        self.login_username = username
        self.login_password = password
        self.client = None
        self.client_kwargs = client_kwargs
        self.cluster = cluster
        self._version = None
        self._aclsave_supported = None

        self.client_kwargs.setdefault('socket_connect_timeout', 5)
        self.client_kwargs.setdefault('socket_timeout', 5)
        self.client_kwargs.setdefault('decode_responses', True)

    @property
    def version(self):
        if self._version is None:
            info = self._execute('info', 'server')
            self._version = info.get('valkey_version')
        return self._version

    @property
    def aclsave_supported(self):
        if self._aclsave_supported is None:
            result = self._execute('config_get', args=['aclfile'])

            self._aclsave_supported = True if result.get('aclfile', '') else False
        return self._aclsave_supported

    def _connect(self):
        if not self.client:
            try:
                if self.cluster:
                    self.client = ValkeyCluster(
                        host=self.login_host,
                        port=self.login_port,
                        username=self.login_username,
                        password=self.login_password,
                        **self.client_kwargs
                    )
                else:
                    self.client = Valkey(
                        host=self.login_host,
                        port=self.login_port,
                        username=self.login_username,
                        password=self.login_password,
                        **self.client_kwargs
                    )
                self.client.ping()
            except valkey.exceptions.ConnectionError as e:
                self.module.fail_json(
                    msg=f"Failed to connect to Valkey at {self.login_host}:{self.login_port} with user '{self.login_username}': {to_native(e)}")
            except valkey.exceptions.AuthenticationError as e:
                self.module.fail_json(
                    msg=f"Authentication failed for user '{self.login_username}' when connecting to Valkey: {to_native(e)}")
            except Exception as e:
                self.module.fail_json(msg=f"Unexpected error: {to_native(e)}")

    def _execute(self, cmd_name, *args, **kwargs):
        try:
            self._connect()
            method = getattr(self.client, cmd_name)
            return method(*args, **kwargs)
        except valkey.exceptions.ResponseError as e:
            self.module.fail_json(msg=f"Error executing command '{cmd_name}': {to_native(e)}")
        except AttributeError as e:
            self.module.fail_json(msg=f"Command '{cmd_name}' not supported by this Valkey version: {to_native(e)}")
