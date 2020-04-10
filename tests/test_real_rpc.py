import os

import pytest

from aioeos import EosTransaction
from aioeos.contracts import eosio_token


@pytest.mark.skipif(
    os.environ.get('DISABLE_RPC_TESTS'),
    reason='RPC tests are disabled'
)
async def test_sign_and_push_transaction(rpc, main_account, second_account):
    action = eosio_token.transfer(
        from_addr=main_account.name,
        to_addr=second_account.name,
        quantity='1.0000 EOS',
        authorization=[main_account.authorization('active')]
    )

    block = await rpc.get_head_block()

    transaction = EosTransaction(
        ref_block_num=block['block_num'] & 65535,
        ref_block_prefix=block['ref_block_prefix'],
        actions=[action]
    )

    # would throw an exception if something went wrong
    await rpc.sign_and_push_transaction(transaction, keys=[main_account.key])
