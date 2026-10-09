from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import pytest
from importlib.util import find_spec
import valkey.exceptions

from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey_client import ValkeyClient


@pytest.fixture
def valkey_client(mocker):
    mock_module = mocker.MagicMock()

    if not find_spec("valkey"):
        pytest.skip("valkey Python package is not installed")
    return ValkeyClient(module=mock_module)


def test_valkey_client_initialization(valkey_client):
    assert valkey_client.login_host == 'localhost'
    assert valkey_client.login_port == 6379
    assert valkey_client.login_username == 'default'
    assert valkey_client.login_password is None
    assert valkey_client.client_kwargs['socket_connect_timeout'] == 5
    assert valkey_client.client_kwargs['socket_timeout'] == 5
    assert valkey_client.client_kwargs['decode_responses'] is True


def test_valkey_client_connection(valkey_client):
    try:
        valkey_client._connect()
        assert valkey_client.client is not None
    except Exception as e:
        pytest.fail(f"Connection to Valkey failed: {e}")


def test_valkey_client_version_caching(valkey_client, mocker):
    mocker.patch.object(valkey_client, '_execute', return_value={'valkey_version': '9.0.0', 'valkey_release_stage': 'ga'})
    version = valkey_client.version

    assert version['full'] == '9.0.0'
    valkey_client._execute.assert_called_once_with('info', 'server')


def test_acl_save_not_supported(valkey_client, mocker):
    mocker.patch.object(valkey_client, '_execute', return_value={'aclfile': ''})

    assert valkey_client.aclsave_supported is False
    valkey_client.aclsave_supported
    valkey_client._execute.assert_called_once()


def test_acl_save_supported(valkey_client, mocker):
    mocker.patch.object(valkey_client, '_execute', return_value={'aclfile': '/valkey.acl'})

    assert valkey_client.aclsave_supported is True
    valkey_client.aclsave_supported
    valkey_client._execute.assert_called_once()


def test_valkey_client_missing_package(mocker):
    mock_module = mocker.MagicMock()
    mock_module.fail_json.side_effect = SystemExit
    mocker.patch('ansible_collections.rkozlo.valkey.plugins.module_utils.valkey_client.HAS_VALKEY_PACKAGE', False)

    with pytest.raises(SystemExit):
        ValkeyClient(module=mock_module)
    assert 'valkey' in mock_module.fail_json.call_args.kwargs['msg']


@pytest.fixture
def connected_client(valkey_client, mocker):
    valkey_client._client = mocker.MagicMock()
    valkey_client.module.fail_json.side_effect = SystemExit
    return valkey_client


@pytest.mark.parametrize("exception,expected_msg", [
    (valkey.exceptions.ResponseError('ERR wrong number of arguments'), "Error executing command 'get'"),
    (valkey.exceptions.NoPermissionError('NOPERM'), "Error executing command 'get'"),
    (valkey.exceptions.TimeoutError('Timeout reading from socket'), "Command 'get' timed out"),
    (valkey.exceptions.ConnectionError('Connection closed by server'), "Lost connection to localhost:6379"),
    (valkey.exceptions.BusyLoadingError('Loading'), "Lost connection to localhost:6379"),
    (valkey.exceptions.ValkeyError('Something else'), "Valkey error executing command 'get'"),
    (TypeError('get() takes 2 positional arguments'), "Invalid arguments for 'get'"),
])
def test_execute_handled_errors(connected_client, exception, expected_msg):
    connected_client._client.get.side_effect = exception

    with pytest.raises(SystemExit):
        connected_client._execute('get', 'key')
    assert expected_msg in connected_client.module.fail_json.call_args.kwargs['msg']


def test_execute_unknown_command(connected_client):
    connected_client._client.not_existing = None

    with pytest.raises(SystemExit):
        connected_client._execute('not_existing')
    assert "is not available in valkey-py" in connected_client.module.fail_json.call_args.kwargs['msg']


def test_execute_attribute_error_not_masked(connected_client):
    connected_client._client.get.side_effect = AttributeError('internal bug')

    with pytest.raises(AttributeError):
        connected_client._execute('get', 'key')
    connected_client.module.fail_json.assert_not_called()


def test_execute_success(connected_client):
    connected_client._client.get.return_value = 'value'

    assert connected_client._execute('get', 'key') == 'value'
    connected_client._client.get.assert_called_once_with('key')
