import traceback

from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.text.converters import to_native

try:
    from valkey import Valkey
    from valkey.cluster import ValkeyCluster
    import valkey.exceptions
    HAS_VALKEY_PACKAGE = True
    VALKEY_IMPORT_ERROR = None
except ImportError:
    HAS_VALKEY_PACKAGE = False
    VALKEY_IMPORT_ERROR = traceback.format_exc()
    Valkey = None
    ValkeyCluster = None


class ValkeyClient:
    def __init__(self, module, cluster=False, host='localhost', port=6379, username='default', password=None, **client_kwargs):
        if not HAS_VALKEY_PACKAGE:
            module.fail_json(msg=missing_required_lib('valkey'), exception=VALKEY_IMPORT_ERROR)
        if cluster and client_kwargs.get('db'):
            module.fail_json(msg="login_db is not supported in cluster mode. Valkey cluster uses only database 0.")
        self.module = module
        self.login_host = host
        self.login_port = port
        self.login_username = username
        self.login_password = password
        self.client_kwargs = client_kwargs
        self.cluster = cluster
        self._client = None
        self._version = None
        self._aclsave_supported = None
        self._config_rewrite_supported = None

        self.client_kwargs.setdefault('socket_connect_timeout', 5)
        self.client_kwargs.setdefault('socket_timeout', 5)
        self.client_kwargs.setdefault('decode_responses', True)

    @property
    def client(self):
        if not self._client:
            if self.cluster:
                self._client = ValkeyCluster(
                    host=self.login_host,
                    port=self.login_port,
                    username=self.login_username,
                    password=self.login_password,
                    **self.client_kwargs
                )
            else:
                self._client = Valkey(
                    host=self.login_host,
                    port=self.login_port,
                    username=self.login_username,
                    password=self.login_password,
                    **self.client_kwargs
                )
        return self._client

    @property
    def version(self):
        if self._version is None:
            self._fetch_server_section()
        return self._version

    def _fetch_server_section(self):
        info = self._execute('info', 'server')
        ver = info.get('valkey_version')
        config_file_exists = False if info.get('config_file', '') == '' else True
        splited = ver.split('.')
        self._version = {
            'full': ver,
            'major': splited[0],
            'minor': splited[1],
            'patch': splited[2],
        }
        self._config_rewrite_supported = config_file_exists

    @property
    def aclsave_supported(self):
        if self._aclsave_supported is None:
            result = self._execute('config_get', args=['aclfile'])

            self._aclsave_supported = True if result.get('aclfile', '') else False
        return self._aclsave_supported

    @property
    def config_rewrite_supported(self):
        if self._config_rewrite_supported is None:
            self._fetch_server_section()
        return self._config_rewrite_supported

    def _connect(self):
        if not self._client:
            try:
                self.client.ping()
            except valkey.exceptions.AuthenticationError as e:
                self.module.fail_json(
                    msg=f"Authentication failed for user '{self.login_username}' when connecting to Valkey: {to_native(e)}")
            except valkey.exceptions.ConnectionError as e:
                self.module.fail_json(
                    msg=f"Failed to connect to Valkey at {self.login_host}:{self.login_port} with user '{self.login_username}': {to_native(e)}")
            except Exception as e:
                self.module.fail_json(msg=f"Unexpected error: {to_native(e)}")

    def _execute(self, cmd_name, *args, **kwargs):
        self._connect()
        method = getattr(self.client, cmd_name, None)
        if not callable(method):
            self.module.fail_json(msg=f"Command '{cmd_name}' is not available in valkey-py {valkey.__version__}.")
        try:
            return method(*args, **kwargs)
        except valkey.exceptions.ResponseError as e:
            self.module.fail_json(msg=f"Error executing command '{cmd_name}': {to_native(e)}")
        except valkey.exceptions.TimeoutError as e:
            self.module.fail_json(
                msg=f"Command '{cmd_name}' timed out: {to_native(e)}. Consider raising socket_timeout in client_kwargs.")
        except valkey.exceptions.ConnectionError as e:
            self.module.fail_json(
                msg=f"Lost connection to {self.login_host}:{self.login_port} while executing '{cmd_name}': {to_native(e)}")
        except valkey.exceptions.ValkeyError as e:
            self.module.fail_json(msg=f"Valkey error executing command '{cmd_name}': {to_native(e)}")
        # Mostly wrong args passed to valkey_exec.
        except TypeError as e:
            self.module.fail_json(msg=f"Invalid arguments for '{cmd_name}': {to_native(e)}")
