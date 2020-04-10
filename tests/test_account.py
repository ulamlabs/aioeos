import pytest

from aioeos import EosAccount, EosKey


def test_new_account():
    account_1 = EosAccount(name='account1')
    account_2 = EosAccount(name='account2')
    assert account_1.key != account_2.key


def test_only_one_key():
    key = EosKey()

    # this is fine
    EosAccount(name='account', key=key)

    # this is also fine
    EosAccount(name='account', private_key=key.to_wif())
    EosAccount(name='account', private_key=key.to_pvt())
    EosAccount(name='account', public_key=key.to_public())

    # this isn't
    with pytest.raises(AssertionError):
        EosAccount(name='account', key=key, public_key=key.to_public())

    # absolutely wrong
    with pytest.raises(AssertionError):
        EosAccount(
            name='account',
            key=key,
            public_key=key.to_public(),
            private_key=key.to_wif()
        )


def test_account_authorization():
    account = EosAccount(name='account')
    authorization = account.authorization('active')
    assert authorization.actor == account.name
    assert authorization.permission == 'active'


def test_account_permission_level_weight():
    account = EosAccount(name='account')
    authorization = account.authorization('active')
    permission_level_weight = account.permission_level_weight('active', 3)
    assert permission_level_weight.permission == authorization
    assert permission_level_weight.weight == 3
