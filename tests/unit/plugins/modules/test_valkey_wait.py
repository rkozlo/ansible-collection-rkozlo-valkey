from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import pytest
import valkey.exceptions

from ansible_collections.rkozlo.valkey.plugins.modules.valkey_wait import ValkeyWait


@pytest.fixture
def valkey_wait(mocker):
    mock_module = mocker.MagicMock()
    mock_module.check_mode = False
    mock_module.params = {'interval': 1, 'retries': 1, 'state': 'ready', 'conditions': None, 'cluster_conditions': None}
    mock_client = mocker.MagicMock()

    return ValkeyWait(module=mock_module, client=mock_client)


@pytest.mark.parametrize("exception,expected", [
    (None, 'ready'),
    (valkey.exceptions.ConnectionError, 'down'),
    (valkey.exceptions.BusyLoadingError, 'down'),
    (valkey.exceptions.ResponseError, 'rejected'),
])
def test_wait_for_state(valkey_wait, exception, expected):
    valkey_wait.client.client.ping.side_effect = exception

    assert valkey_wait._wait_for_state() == expected
    valkey_wait.module.fail_json.assert_not_called()


def test_wait_for_state_auth_error_fails(valkey_wait):
    valkey_wait.client.client.ping.side_effect = valkey.exceptions.AuthenticationError('invalid password')

    valkey_wait._wait_for_state()

    valkey_wait.module.fail_json.assert_called_once()
    assert 'Authentication failed' in valkey_wait.module.fail_json.call_args.kwargs['msg']


def test_fetch_info_calls_standard_info_once(mocker):
    mock_module = mocker.MagicMock()
    mock_module.params = {'interval': 1, 'retries': 1, 'state': 'ready', 'conditions': None, 'cluster_conditions': None}
    mock_client = mocker.MagicMock()
    mock_client.cluster = False
    mock_client.client.info.return_value = {'role': 'master'}
    valkey_wait = ValkeyWait(module=mock_module, client=mock_client)

    result = valkey_wait._fetch_info()

    assert result == {'role': 'master'}
    mock_client.client.info.assert_called_once_with()
    mock_client.client.cluster.assert_not_called()
    mock_client.client.cluster_info.assert_not_called()


def test_fetch_info_calls_cluster_info_once_when_cluster_mode_enabled(mocker):
    mock_module = mocker.MagicMock()
    mock_module.params = {'interval': 1, 'retries': 1, 'state': 'ready', 'conditions': None, 'cluster_conditions': None}
    mock_client = mocker.MagicMock()
    mock_client.cluster = True
    mock_client.client.cluster_info.return_value = {'cluster_state': 'ok'}
    valkey_wait = ValkeyWait(module=mock_module, client=mock_client)

    result = valkey_wait._fetch_info(cluster=True)

    assert result == {'cluster_state': 'ok'}
    mock_client.client.cluster_info.assert_called_once_with()
    mock_client.client.cluster.assert_not_called()
    mock_client.client.info.assert_not_called()


def test_fetch_info_falls_back_to_cluster_info_command_when_cluster_mode_not_configured(mocker):
    mock_module = mocker.MagicMock()
    mock_module.params = {'interval': 1, 'retries': 1, 'state': 'ready', 'conditions': None, 'cluster_conditions': None}
    mock_client = mocker.MagicMock()
    mock_client.cluster = False
    mock_client.client.cluster.return_value = {'cluster_state': 'ok'}
    valkey_wait = ValkeyWait(module=mock_module, client=mock_client)

    result = valkey_wait._fetch_info(cluster=True)

    assert result == {'cluster_state': 'ok'}
    mock_client.client.cluster.assert_called_once_with('info')
    mock_client.client.cluster_info.assert_not_called()
    mock_client.client.info.assert_not_called()


# Extend with new operators as (value, comparator, expected).
@pytest.mark.parametrize("value,comparator,expected", [
    ('master', '==', 'master'),
    ('== master', '==', 'master'),
    ('  ==   master  ', '==', 'master'),
    ('== foo   bar', '==', 'foo bar'),
    ('foo   bar', '==', 'foo bar'),
    (0, '==', '0'),
    ('== 0', '==', '0'),
    ('==0', '==', '0'),
    ('==master', '==', 'master'),
    ('== =foo', '==', '=foo'),
    ('\t==\tmaster\n', '==', 'master'),
    ('', '==', ''),
    ('!= down', '!=', 'down'),
    ('!=down', '!=', 'down'),
    ('> 1', '>', '1'),
    ('>1', '>', '1'),
    ('>= 2', '>=', '2'),
    ('< 0.5', '<', '0.5'),
    ('<=-1', '<=', '-1'),
    ('<= 1e3', '<=', '1e3'),
])
def test_parse_condition(valkey_wait, value, comparator, expected):
    assert valkey_wait._parse_condition(value) == (comparator, expected)
    valkey_wait.module.fail_json.assert_not_called()


@pytest.mark.parametrize("value", ['= 1', '=1', '=== 1', '=>1', '===', '!', '<>1', '!== 1'])
def test_parse_condition_unsupported_comparator_fails(valkey_wait, value):
    valkey_wait.module.fail_json.side_effect = SystemExit

    with pytest.raises(SystemExit):
        valkey_wait._parse_condition(value)

    assert 'Unsupported comparator' in valkey_wait.module.fail_json.call_args.kwargs['msg']


@pytest.mark.parametrize("value", ['> master', '>=', '< 1 2', '<= True'])
def test_parse_condition_numeric_comparator_requires_number(valkey_wait, value):
    valkey_wait.module.fail_json.side_effect = SystemExit

    with pytest.raises(SystemExit):
        valkey_wait._parse_condition(value)

    assert 'requires numeric value' in valkey_wait.module.fail_json.call_args.kwargs['msg']


# Extend with new comparators as (current, expected, comparator, result).
@pytest.mark.parametrize("current,expected,comparator,result", [
    ('master', 'master', '==', True),
    ('slave', 'master', '==', False),
    (0, '0', '==', True),
    ('1', 1, '==', True),
    (1, 0, '==', False),
    (None, 'up', '==', False),
    ('up', 'down', '!=', True),
    ('down', 'down', '!=', False),
    (1, '1', '!=', False),
    (None, 'down', '!=', False),
    (2, '1', '>', True),
    (1, '1', '>', False),
    (1, '1', '>=', True),
    (0, '1', '>=', False),
    (0, '1', '<', True),
    (1, '1', '<', False),
    (1, '1', '<=', True),
    (2, '1', '<=', False),
    ('10', '9', '>', True),
    (0.25, '0.5', '<', True),
    (1000, '1e3', '>=', True),
    (2 ** 60 + 1, str(2 ** 60), '>', True),
    ('8.0.1', '8', '>', False),
    ('master', '1', '>', False),
    (True, '0', '>', False),
    (None, '0', '>=', False),
])
def test_compare(valkey_wait, current, expected, comparator, result):
    assert valkey_wait._compare(current, expected, comparator) is result
    valkey_wait.module.fail_json.assert_not_called()


def test_compare_defaults_to_equal(valkey_wait):
    assert valkey_wait._compare('ready', 'ready') is True
    assert valkey_wait._compare('down', 'ready') is False


def test_compare_unsupported_comparator_fails(valkey_wait):
    valkey_wait.module.fail_json.side_effect = SystemExit

    with pytest.raises(SystemExit):
        valkey_wait._compare(1, 1, 'unknown')

    assert "Unsupported comparator 'unknown'" in valkey_wait.module.fail_json.call_args.kwargs['msg']


def test_conditions_parsed_into_statistics(mocker):
    mock_module = mocker.MagicMock()
    mock_module.params = {'interval': 1, 'retries': 1, 'state': 'ready', 'conditions': {'role': '== master', 'loading': 0}, 'cluster_conditions': None}

    statistics = ValkeyWait(module=mock_module, client=mocker.MagicMock()).statistics

    assert statistics['role']['comparator'] == '=='
    assert statistics['role']['expected'] == 'master'
    assert statistics['loading']['expected'] == '0'
    assert statistics['state']['comparator'] == '=='


def test_single_statistics_block_builds_condition_stats(mocker):
    mock_module = mocker.MagicMock()
    mock_module.params = {'interval': 1, 'retries': 1, 'state': 'ready', 'conditions': None, 'cluster_conditions': None}
    valkey_wait = ValkeyWait(module=mock_module, client=mocker.MagicMock())

    stats = valkey_wait._single_statistics_block({
        'role': '!= slave',
        'connected_slaves': '>= 1',
        'loading': 0,
    })

    assert set(stats) == {'role', 'connected_slaves', 'loading'}
    assert stats['role']['comparator'] == '!='
    assert stats['role']['expected'] == 'slave'
    assert stats['connected_slaves']['comparator'] == '>='
    assert stats['connected_slaves']['expected'] == '1'
    assert stats['loading']['expected'] == '0'
    assert stats['loading']['last_value'] is None
    assert stats['loading']['is_met'] is False
    assert stats['loading']['current_retry'] == 0
    assert stats['loading']['fail_retries'] == 0


def test_initialize_statistics_without_cluster_block(mocker):
    mock_module = mocker.MagicMock()
    mock_module.params = {
        'interval': 1,
        'retries': 2,
        'state': 'ready',
        'conditions': {'role': 'master', 'connected_slaves': '>= 1'},
        'cluster_conditions': None,
    }

    statistics = ValkeyWait(module=mock_module, client=mocker.MagicMock()).statistics

    assert statistics['state']['expected'] == 'ready'
    assert statistics['state']['comparator'] == '=='
    assert statistics['state']['last_value'] == 'down'
    assert statistics['state']['current_retry'] == 0
    assert statistics['state']['is_met'] is False

    assert statistics['role']['expected'] == 'master'
    assert statistics['role']['last_value'] is None
    assert statistics['role']['current_retry'] == 0
    assert statistics['connected_slaves']['comparator'] == '>='
    assert statistics['connected_slaves']['expected'] == '1'


def test_initialize_statistics_includes_cluster_block_when_configured(mocker):
    mock_module = mocker.MagicMock()
    mock_module.params = {
        'interval': 1,
        'retries': 2,
        'state': 'ready',
        'conditions': {'role': 'master'},
        'cluster_conditions': {'cluster_slots_assigned': '== 16384'},
    }

    statistics = ValkeyWait(module=mock_module, client=mocker.MagicMock()).statistics

    assert statistics['role']['expected'] == 'master'
    assert statistics['role']['last_value'] is None
    assert statistics['role']['current_retry'] == 0
    assert statistics['cluster_slots_assigned']['comparator'] == '=='
    assert statistics['cluster_slots_assigned']['expected'] == '16384'
