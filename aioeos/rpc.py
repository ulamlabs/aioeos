import base64
import binascii
from dataclasses import asdict
import hashlib
from typing import Any, List

from aiohttp import ClientSession
from aioeos import exceptions, serializer
from aioeos.keys import EosKey
from aioeos.types import EosTransaction, is_abi_object


ERROR_NAME_MAP = {
    'exception': exceptions.EosRpcException,
    'deadline_exception': exceptions.EosDeadlineException,
    'action_validate_exception': exceptions.EosActionValidateException,
    'tx_cpu_usage_exceeded': exceptions.EosTxCpuUsageExceededException,
    'tx_net_usage_exceeded': exceptions.EosTxNetUsageExceededException,
    'ram_usage_exceeded': exceptions.EosRamUsageExceededException,
    'eosio_assert_message_exception': exceptions.EosAssertMessageException,
}


def mixed_to_dict(payload: Any):
    """
    Recursively converts payload with mixed ABI objects and dicts to dict
    """
    if isinstance(payload, dict):
        return {k: mixed_to_dict(v) for k, v in payload.items()}
    if is_abi_object(type(payload)):
        return asdict(payload)
    return payload


class EosJsonRpc:
    def __init__(self, url):
        self.URL = url
        self._chain_id = None

    async def post(self, endpoint, json={}):
        async with ClientSession() as session:
            async with session.post(
                f'{self.URL}/v1{endpoint}',
                json=json
            ) as res:
                resp_dict = await res.json(content_type=None)

                # Who needs HTTP status codes, am I right? :D
                if isinstance(resp_dict, dict) and resp_dict.get('code') == 500:
                    error = resp_dict.get('error', {})
                    raise ERROR_NAME_MAP.get(
                        error.get('name'),
                        exceptions.EosRpcException
                    )(error)
                return resp_dict

    async def abi_json_to_bin(self, code, action, args):
        return await self.post(
            '/chain/abi_json_to_bin', {
                'code': code,
                'action': action,
                'args': mixed_to_dict(args)
            }
        )

    async def get_abi(self, account_name: str):
        return await self.post(
            '/chain/get_abi', {
                'account_name': account_name
            }
        )

    async def get_account(self, account_name: str):
        return await self.post(
            '/chain/get_account', {
                'account_name': account_name
            }
        )

    async def get_block_header_state(self, block_num_or_id):
        return await self.post(
            '/chain/get_block_header_state', {
                'block_num_or_id': block_num_or_id
            }
        )

    async def get_block(self, block_num_or_id):
        return await self.post(
            '/chain/get_block', {
                'block_num_or_id': block_num_or_id
            }
        )

    async def get_code(self, account_name: str):
        return await self.post(
            '/chain/get_code', {
                'account_name': account_name
            }
        )

    async def get_currency_balance(self, code: str, account: str, symbol: str):
        return await self.post(
            '/chain/get_currency_balance', {
                'code': code,
                'account': account,
                'symbol': symbol
            }
        )

    async def get_currency_stats(self, code: str, symbol: str):
        return await self.post(
            '/chain/get_currency_stats', {
                'code': code,
                'symbol': symbol
            }
        )

    async def get_info(self):
        return await self.post('/chain/get_info')

    async def get_chain_id(self):
        if not self._chain_id:
            info = await self.get_info()
            self._chain_id = binascii.unhexlify(info['chain_id'])
        return self._chain_id

    async def get_head_block(self):
        info = await self.get_info()
        return await self.get_block(info['head_block_num'])

    async def get_producer_schedule(self):
        return await self.post('/chain/get_producer_schedule')

    async def get_producers(self, json=True, lower_bound='', limit=50):
        return await self.post(
            '/chain/get_producers', {
                'json': json,
                'lower_bound': lower_bound,
                'limit': limit
            }
        )

    async def get_raw_code_and_abi(self, account_name: str):
        return await self.post(
            '/chain/get_raw_code_and_abi', {
                'account_name': account_name
            }
        )

    async def get_raw_abi(self, account_name: str):
        response = await self.post(
            '/chain/get_raw_code_and_abi', {
                'account_name': account_name
            }
        )
        return {
            'account_name': response.get('account_name'),
            'abi': base64.b64decode(response.get('abi'))
        }

    async def get_table_rows(
        self, code, scope, table, table_key='', lower_bound='', upper_bound='',
        index_position=1, key_type='', limit=10, reverse=False,
        show_payer=False, json=True
    ):
        return await self.post(
            '/chain/get_table_rows', {
                'json': json,
                'code': code,
                'scope': scope,
                'table': table,
                'table_key': table_key,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'index_position': index_position,
                'key_type': key_type,
                'limit': limit,
                'reverse': reverse,
                'show_payer': show_payer
            }
        )

    async def get_table_by_scope(
        self, code, table, lower_bound='', upper_bound='', limit=10
    ):
        return await self.post(
            '/chain/get_table_by_scope', {
                'code': code,
                'table': table,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'limit': limit
            }
        )

    async def get_required_keys(self, transaction, available_keys):
        return await self.post(
            '/chain/get_required_keys', {
                'transaction': transaction,
                'available_keys': available_keys
            }
        )

    async def sign_and_push_transaction(
        self,
        transaction: EosTransaction,
        *,
        context_free_bytes: bytes = bytes(32),
        keys: List[EosKey] = []
    ):
        for action in transaction.actions:
            if isinstance(action.data, dict):
                abi_bin = await self.abi_json_to_bin(
                    action.account, action.name, action.data
                )
                action.data = binascii.unhexlify(abi_bin['binargs'])

        chain_id = await self.get_chain_id()
        serialized_transaction = serializer.serialize(transaction)

        digest = hashlib.sha256(
            b''.join((chain_id, serialized_transaction, context_free_bytes))
        ).digest()

        return await self.push_transaction(
            signatures=[key.sign(digest) for key in keys],
            serialized_transaction=(
                binascii.hexlify(serialized_transaction).decode()
            )
        )

    async def push_transaction(self, signatures, serialized_transaction):
        return await self.post(
            '/chain/push_transaction', {
                'signatures': signatures,
                'compression': 0,
                'packed_context_free_data': '',
                'packed_trx': serialized_transaction
            }
        )

    async def get_db_size(self):
        return await self.post('/db_size/get')

    async def get_actions(self, account_name: str, pos=None, offset=None):
        return await self.post(
            '/history/get_actions', {
                'account_name': account_name,
                'pos': pos,
                'offset': offset
            }
        )

    async def get_transaction(self, tx_id: str, block_num_hint=None):
        return await self.post(
            '/history/get_transaction', {
                'id': tx_id,
                'block_num_hint': block_num_hint
            }
        )

    async def get_key_accounts(self, public_key):
        return await self.post(
            '/history/get_key_accounts', {
                'public_key': public_key
            }
        )

    async def get_controlled_accounts(self, account_name: str):
        return await self.post(
            '/history/get_controlled_accounts', {
                'controlling_account': account_name
            }
        )
