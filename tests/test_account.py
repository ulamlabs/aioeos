import pytest

from aioeos.account import EOSAccount
from aioeos.keys import EOSKey


def test_new_account():
    account_1 = EOSAccount(name='account1')
    account_2 = EOSAccount(name='account2')
    assert account_1.key != account_2.key


def test_only_one_key():
    key = EOSKey()

    # this is fine
    EOSAccount(name='account', key=key)

    # this isn't
    with pytest.raises(AssertionError):
        EOSAccount(name='account', key=key, public_key=key.to_public())

    # absolutely wrong
    with pytest.raises(AssertionError):
        EOSAccount(
            name='account',
            key=key,
            public_key=key.to_public(),
            private_key=key.to_wif()
        )


def test_account_authorization():
    account = EOSAccount(name='account')
    authorization = account.authorization('active')
    assert authorization.actor == account.name
    assert authorization.permission == 'active'


def test_account_permission_level_weight():
    account = EOSAccount(name='account')
    authorization = account.authorization('active')
    permission_level_weight = account.permission_level_weight('active', 3)
    assert permission_level_weight.permission == authorization
    assert permission_level_weight.weight == 3
