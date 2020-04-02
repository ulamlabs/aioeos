import asyncio

from aioresponses import aioresponses
import pytest

from aioeos import exceptions
from aioeos.rpc import EosJsonRpc


@pytest.fixture
def rpc():
    return EosJsonRpc('http://mock.rpc.url')


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
