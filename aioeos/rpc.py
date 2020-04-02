import base64
from aiohttp import ClientSession
from aioeos import exceptions


ERROR_NAME_MAP = {
    'exception': exceptions.EosRpcException,
    'deadline_exception': exceptions.EosDeadlineException,
    'action_validate_exception': exceptions.EosActionValidateException,
    'tx_cpu_usage_exceeded': exceptions.EosTxCpuUsageExceededException,
    'tx_net_usage_exceeded': exceptions.EosTxNetUsageExceededException,
    'ram_usage_exceeded': exceptions.EosRamUsageExceededException,
    'eosio_assert_message_exception': exceptions.EosAssertMessageException,
}


class EosJsonRpc:
    def __init__(self, url):
        self.URL = url

    async def post(self, endpoint, json={}):
        async with ClientSession() as session:
            async with session.post(
                f'{self.URL}/v1{endpoint}',
                json=json
            ) as res:
                resp_dict = await res.json(content_type=None)

                # Who needs HTTP status codes, am I right? :D
                if resp_dict.get('code') == 500:
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
                'args': args
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
