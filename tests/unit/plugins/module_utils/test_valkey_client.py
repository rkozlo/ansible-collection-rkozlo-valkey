from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import pytest
from importlib.util import find_spec

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

    assert version == '9.0.0'
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
