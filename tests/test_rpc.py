import asyncio
import binascii
from dataclasses import dataclass
from datetime import datetime

from aioresponses import aioresponses
import pytest
from yarl import URL

from aioeos import exceptions, EosAction, EosTransaction
from aioeos.types import BaseAbiObject, UInt8


@pytest.fixture
def mock_post(mocker, rpc):
    return mocker.patch.object(
        rpc, 'post', side_effect=asyncio.coroutine(lambda *args, **kwargs: {})
    )


@pytest.fixture
def ar():
    with aioresponses() as m:
        yield m


async def test_error_mapping(rpc, ar):
    mock_url = f'{rpc.URL}/v1/mock'

    # known exception
    ar.post(
        mock_url,
        payload={
            'code': 500,
            'error': {
                'name': 'ram_usage_exceeded'
            }
        }
    )
    with pytest.raises(exceptions.EosRamUsageExceededException):
        await rpc.post('/mock')

    # unknown exception
    ar.post(
        mock_url,
        payload={
            'code': 500,
            'error': {
                'name': 'everything_is_fine'
            }
        }
    )
    with pytest.raises(exceptions.EosRpcException):
        await rpc.post('/mock')

    payload = {
        'ok': 'yes'
    }
    ar.post(mock_url, payload=payload)
    assert await rpc.post('/mock') == payload


async def test_abi_json_to_bin(rpc, mock_post):
    await rpc.abi_json_to_bin('eosio.token', 'send', {})
    mock_post.assert_called_with(
        '/chain/abi_json_to_bin',
        {
            'code': 'eosio.token',
            'action': 'send',
            'args': {}
        }
    )


async def test_get_abi(rpc, mock_post):
    await rpc.get_abi('eosio.token')
    mock_post.assert_called_with(
        '/chain/get_abi', {'account_name': 'eosio.token'}
    )


async def test_get_account(rpc, mock_post):
    await rpc.get_account('eosio')
    mock_post.assert_called_with(
        '/chain/get_account', {'account_name': 'eosio'}
    )


async def test_get_block_header_state(rpc, mock_post):
    await rpc.get_block_header_state(3)
    mock_post.assert_called_with(
        '/chain/get_block_header_state', {'block_num_or_id': 3}
    )


async def test_get_block(rpc, mock_post):
    await rpc.get_block(3)
    mock_post.assert_called_with(
        '/chain/get_block', {'block_num_or_id': 3}
    )


async def test_get_code(rpc, mock_post):
    await rpc.get_code('eosio')
    mock_post.assert_called_with(
        '/chain/get_code', {'account_name': 'eosio'}
    )


async def test_get_currency_balance(rpc, mock_post):
    await rpc.get_currency_balance('eosio', 'eosio', 'EOS')
    mock_post.assert_called_with(
        '/chain/get_currency_balance',
        {
            'code': 'eosio',
            'account': 'eosio',
            'symbol': 'EOS'
        }
    )


async def test_get_currency_stats(rpc, mock_post):
    await rpc.get_currency_stats('eosio', 'EOS')
    mock_post.assert_called_with(
        '/chain/get_currency_stats',
        {
            'code': 'eosio',
            'symbol': 'EOS'
        }
    )


async def test_get_info(rpc, mock_post):
    await rpc.get_info()
    mock_post.assert_called_with('/chain/get_info')


async def test_get_chain_id(rpc, ar):
    mock_url = f'{rpc.URL}/v1/chain/get_info'
    hex_chain_id = (
        '7479dd536fa543a6e5faafe8f90132f8d1aab58c746d7d7a4e01c10ea091e25a'
    )
    expected_chain_id = binascii.unhexlify(hex_chain_id)
    ar.post(mock_url, payload={'chain_id': hex_chain_id})

    assert await rpc.get_chain_id() == expected_chain_id
    assert len(ar._responses) == 1

    # make sure it's cached
    assert await rpc.get_chain_id() == expected_chain_id
    assert len(ar._responses) == 1


async def test_get_producer_schedule(rpc, mock_post):
    await rpc.get_producer_schedule()
    mock_post.assert_called_with('/chain/get_producer_schedule')


async def test_get_producers(rpc, mock_post):
    await rpc.get_producers()
    mock_post.assert_called_with(
        '/chain/get_producers',
        {
            'json': True,
            'lower_bound': '',
            'limit': 50
        }
    )


async def test_get_raw_code_and_abi(rpc, mock_post):
    await rpc.get_raw_code_and_abi('eosio.token')
    mock_post.assert_called_with(
        '/chain/get_raw_code_and_abi', {'account_name': 'eosio.token'}
    )


async def test_get_raw_abi(rpc, mock_post):
    response = {
        'account_name': 'eosio',
        'abi': 'dGVzdA=='
    }
    mock_post.side_effect = asyncio.coroutine(lambda *args, **kwargs: response)
    raw_abi = await rpc.get_raw_abi('eosio')
    mock_post.assert_called_with(
        '/chain/get_raw_code_and_abi', {'account_name': 'eosio'}
    )
    assert raw_abi == {
        'account_name': 'eosio',
        'abi': 'test'.encode()
    }


async def test_get_table_rows(rpc, mock_post):
    await rpc.get_table_rows('eosio', 'system', 'accounts')
    mock_post.assert_called_with(
        '/chain/get_table_rows',
        {
            'json': True,
            'code': 'eosio',
            'scope': 'system',
            'table': 'accounts',
            'table_key': '',
            'lower_bound': '',
            'upper_bound': '',
            'index_position': 1,
            'key_type': '',
            'limit': 10,
            'reverse': False,
            'show_payer': False
        }
    )


async def test_get_table_by_scope(rpc, mock_post):
    await rpc.get_table_by_scope('eosio', 'accounts')
    mock_post.assert_called_with(
        '/chain/get_table_by_scope',
        {
            'code': 'eosio',
            'table': 'accounts',
            'lower_bound': '',
            'upper_bound': '',
            'limit': 10
        }
    )


async def test_get_required_keys(rpc, mock_post):
    await rpc.get_required_keys('abcd123', [])
    mock_post.assert_called_with(
        '/chain/get_required_keys',
        {
            'transaction': 'abcd123',
            'available_keys': []
        }
    )


async def test_push_transaction(rpc, mock_post):
    await rpc.push_transaction([], 'abcd123')
    mock_post.assert_called_with(
        '/chain/push_transaction',
        {
            'signatures': [],
            'compression': 0,
            'packed_context_free_data': '',
            'packed_trx': 'abcd123'
        }
    )


async def test_get_db_size(rpc, mock_post):
    await rpc.get_db_size()
    mock_post.assert_called_with('/db_size/get')


async def test_get_actions(rpc, mock_post):
    await rpc.get_actions('eosio')
    mock_post.assert_called_with(
        '/history/get_actions',
        {
            'account_name': 'eosio',
            'pos': None,
            'offset': None
        }
    )


async def test_get_transaction(rpc, mock_post):
    await rpc.get_transaction('123abcd')
    mock_post.assert_called_with(
        '/history/get_transaction',
        {
            'id': '123abcd',
            'block_num_hint': None
        }
    )


async def test_get_key_accounts(rpc, mock_post):
    await rpc.get_key_accounts('publickey')
    mock_post.assert_called_with(
        '/history/get_key_accounts', {'public_key': 'publickey'}
    )


async def test_get_controlled_accounts(rpc, mock_post):
    await rpc.get_controlled_accounts('eosio')
    mock_post.assert_called_with(
        '/history/get_controlled_accounts', {'controlling_account': 'eosio'}
    )


async def test_get_head_block(rpc, ar):
    expected_head_block = {
        'block_num': 3,
        'ref_block_prefix': 4
    }
    ar.post(f'{rpc.URL}/v1/chain/get_info', payload={'head_block_num': 3})
    ar.post(f'{rpc.URL}/v1/chain/get_block', payload=expected_head_block)

    assert await rpc.get_head_block() == expected_head_block


@pytest.fixture
def expected_signed_transaction():
    return {
        'compression': 0,
        'packed_context_free_data': '',
        'packed_trx': (
            'a8aaca5d03000400000000000000011032561960aaa833000000000090b1ca015'
            '0c810216395315500000000a8ed3232010300'
        ),
        'signatures': [
            'SIG_K1_Kh65eZiWa3DCMT5UjnZf9tNtG8P4DBgULd1Tq15Hg37LfDTn8jtW6e7Yt'
            'dB3EuANcCC64s445URAkRt27rjWr8WYqZweLH'
        ]
    }


async def test_sign_and_push_transaction_dict_payload(
    rpc, ar, main_account, expected_signed_transaction
):
    ar.post(
        f'{rpc.URL}/v1/chain/get_info',
        payload={'chain_id': '00aabbbccc'}
    )
    ar.post(f'{rpc.URL}/v1/chain/abi_json_to_bin', payload={'binargs': '03'})
    ar.post(f'{rpc.URL}/v1/chain/push_transaction', payload={'code': 200})

    action = EosAction(
        account='aioeos.test1',
        name='test',
        authorization=[main_account.authorization('active')],
        data={'a': 3}
    )
    transaction = EosTransaction(
        expiration=datetime.fromisoformat('2019-11-12T12:50:48.000+00:00'),
        ref_block_num=3,
        ref_block_prefix=4,
        actions=[action]
    )

    await rpc.sign_and_push_transaction(transaction, keys=[main_account.key])
    assert len(ar._responses) == 3
    push_request = ar.requests[
        ('POST', URL('http://127.0.0.1:8888/v1/chain/push_transaction'))
    ][0]
    assert push_request.kwargs['json'] == expected_signed_transaction


async def test_sign_and_push_transaction_bytes_payload(
    rpc, ar, main_account, expected_signed_transaction
):
    ar.post(
        f'{rpc.URL}/v1/chain/get_info',
        payload={'chain_id': '00aabbbccc'}
    )
    ar.post(f'{rpc.URL}/v1/chain/push_transaction', payload={'code': 200})

    action = EosAction(
        account='aioeos.test1',
        name='test',
        authorization=[main_account.authorization('active')],
        data=b'\x03'
    )
    transaction = EosTransaction(
        expiration=datetime.fromisoformat('2019-11-12T12:50:48.000+00:00'),
        ref_block_num=3,
        ref_block_prefix=4,
        actions=[action]
    )

    await rpc.sign_and_push_transaction(transaction, keys=[main_account.key])
    assert len(ar._responses) == 2
    push_request = ar.requests[
        ('POST', URL('http://127.0.0.1:8888/v1/chain/push_transaction'))
    ][0]
    assert push_request.kwargs['json'] == expected_signed_transaction


async def test_sign_and_push_transaction_abi_payload(
    rpc, ar, main_account, expected_signed_transaction
):
    @dataclass
    class Payload(BaseAbiObject):
        a: UInt8

    ar.post(
        f'{rpc.URL}/v1/chain/get_info',
        payload={'chain_id': '00aabbbccc'}
    )
    ar.post(f'{rpc.URL}/v1/chain/push_transaction', payload={'code': 200})

    action = EosAction(
        account='aioeos.test1',
        name='test',
        authorization=[main_account.authorization('active')],
        data=Payload(a=3)
    )
    transaction = EosTransaction(
        expiration=datetime.fromisoformat('2019-11-12T12:50:48.000+00:00'),
        ref_block_num=3,
        ref_block_prefix=4,
        actions=[action]
    )

    await rpc.sign_and_push_transaction(transaction, keys=[main_account.key])
    assert len(ar._responses) == 2
    push_request = ar.requests[
        ('POST', URL('http://127.0.0.1:8888/v1/chain/push_transaction'))
    ][0]
    assert push_request.kwargs['json'] == expected_signed_transaction
