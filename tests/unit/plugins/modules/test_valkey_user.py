from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import pytest

from ansible_collections.rkozlo.valkey.plugins.modules.valkey_user import ValkeyUser


@pytest.fixture
def valkey_user(mocker):
    mock_module = mocker.MagicMock()
    mock_module.check_mode = False
    mock_client = mocker.MagicMock()

    # if not find_spec("valkey"):
    #     pytest.skip("valkey Python package is not installed")
    return ValkeyUser(module=mock_module, client=mock_client, name='test_user')


@pytest.mark.parametrize("passwords,hashed_passwords,expected_pass,expected_hash", [
    ([], [], [], []),
    (['test'], [], ['+test'], []),
    ([], ['hash'], [], ['+hash']),
    ([], ['hash', 'hash2'], [], ['+hash', '+hash2']),
    (['test', 'test2'], ['hash'], ['+test', '+test2'], ['+hash']),
])
def test_extract_passwords(valkey_user, passwords, hashed_passwords, expected_pass, expected_hash):

    res_pass, res_hash = valkey_user._extract_passwords(passwords, hashed_passwords)

    assert res_pass == expected_pass
    assert res_hash == expected_hash


@pytest.mark.parametrize("passwords,hashed_passwords,expected", [
    ([], [], []),
    (['test'], [], ['9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08']),
    (
        [],
        ['9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'],
        ['9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08']
    ),
    (
        ['test', 'test2'],
        [],
        [
            '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
            '60303ae22b998861bce3b28f33eec1be758a213c86c93c076dbe9f558c11c752'
        ]
    ),
    (
        [],
        [
            '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
            '60303ae22b998861bce3b28f33eec1be758a213c86c93c076dbe9f558c11c752'
        ],
        [
            '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
            '60303ae22b998861bce3b28f33eec1be758a213c86c93c076dbe9f558c11c752'
        ]
    ),
    (
        ['test'],
        ['60303ae22b998861bce3b28f33eec1be758a213c86c93c076dbe9f558c11c752'],
        [
            '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
            '60303ae22b998861bce3b28f33eec1be758a213c86c93c076dbe9f558c11c752'
        ]
    ),
    # Password and hash equal
    (
        ['test'],
        ['9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'],
        ['9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08']
    )
])
def test_normalize_passwords_and_hashes(valkey_user, passwords, hashed_passwords, expected):
    result = valkey_user._normalize_passwords_and_hashes(passwords, hashed_passwords)

    assert set(result) == set(expected)


@pytest.mark.parametrize("desired,current,expected", [
    ([], [], True),
    (
        ['9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'],
        [],
        False
    ),
    (
        [],
        ['9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'],
        False
    ),
    (
        ['9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'],
        ['9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'],
        True
    ),
    (
        [
            '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
            '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'
        ],
        ['9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'],
        True
    ),
    (
        ['9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'],
        [
            '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
            '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'],
        True
    ),
    (
        ['9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a0a'],
        [
            '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
            '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'
        ],
        False
    ),

])
def test_compare_passwords(valkey_user, desired, current, expected):
    valkey_user._passwords = current

    result = valkey_user._compare_passwords(desired)

    assert result == expected


@pytest.mark.parametrize("compare_result,reset_passwords,current_set,normalized_set,expected", [
    (True, False, [], [], False),                       # Already equal
    (True, True, [], [], False),                        # Already equal reset
    (False, False, [], ['a'], True),                    # Not equal
    (False, True, [], ['a'], True),                     # Not equal reset
    (False, False, ['a'], ['b'], True),                 # Not equal, replace → update
    (False, True, ['a'], ['b'], True),                  # Not equal, replace reset → update
    (False, False, ['a', 'b'], ['a'], False),           # Subset exists → no update
    (False, True, ['a', 'b'], ['a'], True),             # Subset exists not equal reset → update
    (False, False, ['a', 'b'], ['a', 'b'], False),      # Subset equal → no update
    (True, True, ['a', 'b'], ['a', 'b'], False),        # Subset equal reset → no update
])
def test_passwords_needs_update(valkey_user, mocker, compare_result, reset_passwords, current_set, normalized_set, expected):
    mocker.patch.object(valkey_user, '_normalize_passwords_and_hashes', return_value=normalized_set)
    mocker.patch.object(valkey_user, '_compare_passwords', return_value=compare_result)
    valkey_user._passwords = current_set

    result = valkey_user._passwords_needs_update(['dummy'], None, reset_passwords)

    assert result is expected


@pytest.mark.parametrize("reset_key_patterns, key_patterns, current, expected", [
    (False, [], [], False),                         # Equal empty,
    (True, [], [], False),                          # Equal empty reset
    (False, ['~*'], [], True),                      # Not equal
    (True, ['~*'], [], True),                       # Not equal reset
    (False, ['~*'], ['~*'], False),                 # Equal
    (True, ['~*'], ['~*'], False),                  # Equal reset
    (False, ['~*', 'cache*'], ['~*'], True),        # Not equal
    (True, ['~*', 'cache*'], ['~*'], True),         # Not equal reset
    (False, ['cache*'], ['~*', 'cache*'], False),   # Subset part of
    (True, ['cache*'], ['~*', 'cache*'], True),     # Subset port of reset
])
def test_key_patterns_needs_update(valkey_user, key_patterns, current, reset_key_patterns, expected,):
    valkey_user._key_patterns = current
    result = valkey_user._key_patterns_needs_update(key_patterns, reset_key_patterns)

    assert result is expected


@pytest.mark.parametrize("categories,expected", [
    ([], ['-@all']),
    (['+@all'], ['+@all']),
    (['-@all'], ['-@all']),
    (['+@read'], ['-@all', '+@read']),
    (['+@read', '+@connection'], ['-@all', '+@read', '+@connection']),
])
def test_normalize_categories(valkey_user, categories, expected):
    result = valkey_user._normalize_categories(categories)

    assert result == expected


@pytest.mark.parametrize("key_patterns,expected", [
    ([], []),
    ([''], ['~']),
    (['~'], ['~']),
    (['cache*'], ['~cache*']),
    (['cache*', 'db*'], ['~cache*', '~db*']),
    (['%R~cache*'], ['%R~cache*']),
    (['%R~cache*', '%R~db*'], ['%R~cache*', '%R~db*']),
    (['%RW~cache*'], ['~cache*']),
    (['~cache*'], ['~cache*']),
    (['%rw~web:*', '%w~db:*', '%r~mon:*'], ['~web:*', '%W~db:*', '%R~mon:*'])
])
def test_normalize_key_patterns_correct_patterns(valkey_user, key_patterns, expected):
    result = valkey_user._normalize_key_patterns(key_patterns)

    valkey_user.module.fail_json.assert_not_called()
    assert result == expected


@pytest.mark.parametrize("key_patterns", [
    ['%cache'],
    ['%'],
    ['%Ra~'],
    ['%WA'],
    ['%key:*']
])
def test_normalize_key_patterns_wrong_patterns(valkey_user, key_patterns):
    valkey_user._normalize_key_patterns(key_patterns)

    valkey_user.module.fail_json.assert_called_once()


@pytest.mark.parametrize("reset_channels, channels, current, expected", [
    (False, [], [], False),
    (True, [], [], False),
    (False, ['allchannels'], [], True),
    (False, ['allchannels'], ['&allchannels'], False),
    (True, ['allchannels'], ['&allchannels'], False),
    (False, ['allchannels', '&data.?'], ['&allchannels'], True),
    (True, ['data.?'], ['&allchannels', '&data.?'], True),
    (False, ['data.?'], ['&allchannels', '&data.?'], False),
    (False, ['&data.?'], ['&allchannels', '&data.?'], True),
])
def test_channels_needs_update(valkey_user, reset_channels, channels, current, expected,):
    valkey_user._channels = current
    result = valkey_user._channels_needs_update(channels, reset_channels)

    assert result is expected


def test_needs_update_enabled_change_from_false_to_true(valkey_user, mocker):
    """Test update needed when enabled status changes from False to True"""
    mocker.patch.object(valkey_user, '_passwords_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_key_patterns_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_channels_needs_update', return_value=False)
    valkey_user._enabled = False
    valkey_user._commands = []
    valkey_user._categories = []

    result = valkey_user._needs_update(
        enabled=True, commands=[], categories=[],
        key_patterns=[], channels=[], passwords=[], hashed_passwords=[]
    )

    assert result is True


def test_needs_update_enabled_change_from_true_to_false(valkey_user, mocker):
    """Test update needed when enabled status changes from True to False"""
    mocker.patch.object(valkey_user, '_passwords_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_key_patterns_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_channels_needs_update', return_value=False)
    valkey_user._enabled = True
    valkey_user._commands = []
    valkey_user._categories = []

    result = valkey_user._needs_update(
        enabled=False, commands=[], categories=[],
        key_patterns=[], channels=[], passwords=[], hashed_passwords=[]
    )

    assert result is True


def test_needs_update_plain_no_change_needed(valkey_user, mocker):
    """Test no update when everything matches"""
    mocker.patch.object(valkey_user, '_passwords_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_key_patterns_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_channels_needs_update', return_value=False)
    valkey_user._enabled = True
    valkey_user._commands = []
    valkey_user._categories = []

    result = valkey_user._needs_update(
        enabled=True, commands=[], categories=[],
        key_patterns=[], channels=[], passwords=[], hashed_passwords=[]
    )

    assert result is False


def test_needs_update_no_change_needed(valkey_user, mocker):
    """Test no update when everything matches"""
    mocker.patch.object(valkey_user, '_passwords_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_key_patterns_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_channels_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_categories_needs_update', return_value=False)
    valkey_user._enabled = True
    valkey_user._commands = ['get', 'set']
    valkey_user._categories = ['@admin']

    result = valkey_user._needs_update(
        enabled=True, commands=['get', 'set'], categories=['@admin'],
        key_patterns=[], channels=[], passwords=[], hashed_passwords=[]
    )

    assert result is False


def test_needs_update_passwords_need_update(valkey_user, mocker):
    """Test update needed when passwords need changing"""
    mocker.patch.object(valkey_user, '_passwords_needs_update', return_value=True)
    mocker.patch.object(valkey_user, '_key_patterns_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_channels_needs_update', return_value=False)
    valkey_user._enabled = True
    valkey_user._commands = []
    valkey_user._categories = []

    result = valkey_user._needs_update(
        enabled=True, commands=[], categories=[],
        key_patterns=[], channels=[], passwords=['newpass'], hashed_passwords=[]
    )

    assert result is True


def test_needs_update_key_patterns_need_update(valkey_user, mocker):
    """Test update needed when key patterns need changing"""
    mocker.patch.object(valkey_user, '_passwords_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_key_patterns_needs_update', return_value=True)
    mocker.patch.object(valkey_user, '_channels_needs_update', return_value=False)
    valkey_user._enabled = True
    valkey_user._commands = []
    valkey_user._categories = []

    result = valkey_user._needs_update(
        enabled=True, commands=[], categories=[],
        key_patterns=['cache:*', 'user:*'], channels=[], passwords=[], hashed_passwords=[]
    )

    assert result is True


def test_needs_update_channels_need_update(valkey_user, mocker):
    """Test update needed when channel patterns need changing"""
    mocker.patch.object(valkey_user, '_passwords_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_key_patterns_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_channels_needs_update', return_value=True)
    valkey_user._enabled = True
    valkey_user._commands = []
    valkey_user._categories = []

    result = valkey_user._needs_update(
        enabled=True, commands=[], categories=[],
        key_patterns=[], channels=['chat:*', 'alerts'], passwords=[], hashed_passwords=[]
    )

    assert result is True


def test_needs_update_commands_different(valkey_user, mocker):
    """Test update needed when command list differs"""
    mocker.patch.object(valkey_user, '_passwords_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_key_patterns_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_channels_needs_update', return_value=False)
    valkey_user._enabled = True
    valkey_user._commands = ['get']
    valkey_user._categories = []

    result = valkey_user._needs_update(
        enabled=True, commands=['get', 'set'], categories=[],
        key_patterns=[], channels=[], passwords=[], hashed_passwords=[]
    )

    assert result is True


def test_needs_update_commands_same_different_order(valkey_user, mocker):
    """Test no update when commands are same regardless of order"""
    mocker.patch.object(valkey_user, '_passwords_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_key_patterns_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_channels_needs_update', return_value=False)
    valkey_user._enabled = True
    valkey_user._commands = ['set', 'get']
    valkey_user._categories = []

    result = valkey_user._needs_update(
        enabled=True, commands=['get', 'set'], categories=[],
        key_patterns=[], channels=[], passwords=[], hashed_passwords=[]
    )

    assert result is False


def test_needs_update_categories_different(valkey_user, mocker):
    """Test update needed when categories differ"""
    mocker.patch.object(valkey_user, '_passwords_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_key_patterns_needs_update', return_value=False)
    mocker.patch.object(valkey_user, '_channels_needs_update', return_value=False)
    valkey_user._enabled = True
    valkey_user._commands = []
    valkey_user._categories = ['@read']

    result = valkey_user._needs_update(
        enabled=True, commands=[], categories=['@admin'],
        key_patterns=[], channels=[], passwords=[], hashed_passwords=[]
    )

    assert result is True
