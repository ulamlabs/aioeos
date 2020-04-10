from aioeos import EosAction
from aioeos.types import EosAuthority
from aioeos.contracts import eosio, eosio_token


def test_eosio_token_transfer():
    assert (
        eosio_token.transfer(
            'myaddress', 'otheraddress', '1.0000 EOS'
        ) == EosAction(
            account='eosio.token',
            name='transfer',
            authorization=[],
            data={
                'from': 'myaddress',
                'to': 'otheraddress',
                'quantity': '1.0000 EOS',
                'memo': ''
            }
        )
    )


def test_eosio_token_close():
    assert (
        eosio_token.close(
            'myaddress', 'EOS'
        ) == EosAction(
            account='eosio.token',
            name='close',
            authorization=[],
            data={
                'owner': 'myaddress',
                'symbol': 'EOS'
            }
        )
    )


def test_eosio_newaccount(main_account):
    authority = EosAuthority(
        threshold=1,
        keys=[main_account.key.to_key_weight(1)]
    )
    assert (
        eosio.newaccount(
            main_account.name, 'eosio2', owner=authority
        ) == EosAction(
            account='eosio',
            name='newaccount',
            authorization=[],
            data={
                'creator': main_account.name,
                'name': 'eosio2',
                'owner': authority,
                'active': authority
            }
        )
    )


def test_eosio_buyrambytes():
    assert (
        eosio.buyrambytes(
            'eosio', 'eosio2', '1000'
        ) == EosAction(
            account='eosio',
            name='buyrambytes',
            authorization=[],
            data={
                'payer': 'eosio',
                'receiver': 'eosio2',
                'bytes': '1000'
            }
        )
    )


def test_eosio_sellram():
    assert (
        eosio.sellram(
            'eosio', '1000'
        ) == EosAction(
            account='eosio',
            name='sellram',
            authorization=[],
            data={
                'account': 'eosio',
                'bytes': '1000'
            }
        )
    )


def test_eosio_delegatebw():
    assert (
        eosio.delegatebw(
            'eosio', 'eosio2', '1.0000 EOS', '2.0000 EOS',
        ) == EosAction(
            account='eosio',
            name='delegatebw',
            authorization=[],
            data={
                'from': 'eosio',
                'receiver': 'eosio2',
                'stake_net_quantity': '1.0000 EOS',
                'stake_cpu_quantity': '2.0000 EOS',
                'transfer': False
            }
        )
    )


def test_eosio_undelegatebw():
    assert (
        eosio.undelegatebw(
            'eosio', 'eosio2', '1.0000 EOS', '2.0000 EOS',
        ) == EosAction(
            account='eosio',
            name='undelegatebw',
            authorization=[],
            data={
                'from': 'eosio',
                'receiver': 'eosio2',
                'unstake_net_quantity': '1.0000 EOS',
                'unstake_cpu_quantity': '2.0000 EOS',
            }
        )
    )
