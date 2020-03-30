# aioeos

[![Documentation Status](https://readthedocs.org/projects/aioeos/badge/?version=latest)](http://aioeos.readthedocs.io/en/latest/?badge=latest) [![codecov](https://codecov.io/gh/ksiazkowicz/aioeos/branch/master/graph/badge.svg)](https://codecov.io/gh/ksiazkowicz/aioeos) ![Python package](https://github.com/ksiazkowicz/aioeos/workflows/Python%20package/badge.svg) ![Upload Python Package](https://github.com/ksiazkowicz/aioeos/workflows/Upload%20Python%20Package/badge.svg)

Async Python library for interacting with EOS.io blockchain. Library consists of an async wrapper for [Nodeos RPC API](https://developers.eos.io/eosio-nodeos/docs), a simple serializer for basic ABI types like transactions and actions and private key management. Helpers for generating actions such as creating new accounts, buying and selling RAM etc. can be imported from `aioeos.contracts` namespace.

Please bear in mind that the serializer is not complete. Action payloads need
to be converted to binary format using `/abi_json_to_bin` endpoint on the RPC node. Use only nodes you trust.

## Usage examples
Converting action payload to binary format:
```
rpc = EosJsonRpc()
response = await rpc.abi_json_to_bin(
    action.account, action.name, action.data
)
action.data = binascii.unhexlify(response['binargs'])
```

Creating a basic transaction:
```
auth = [EosAuthorization(actor=from_addr, permission='active')]
action = await convert_action_abi_to_bin(
    eosio_token.transfer(from_addr, to_addr, amount, authorization=auth)
)

transaction = EosTransaction(
    actions=[
        eosio_token.transfer(from_addr, to_addr, amount, authorization=auth)
    ]
)
keys = [EOSKey(private_key)]
```

```
import binascii
from aioeos import serializer
from aioeos.contracts import eosio_token
from aioeos.keys import EOSKey
from aioeos.rpc import EosJsonRpc
from aioeos.types import EosAuthorization, EosTransaction

async def convert_action_abi_to_bin(action):
    rpc = EosJsonRpc()
    response = await rpc.abi_json_to_bin(
        action.account, action.name, action.data
    )
    action.data = binascii.unhexlify(response['binargs'])
    return action


async def transfer(from_addr, to_addr, amount, private_key):
    rpc = EosJsonRpc()

    auth = [EosAuthorization(actor=from_addr, permission='active')]
    action = await convert_action_abi_to_bin(
        eosio_token.transfer(from_addr, to_addr, amount, authorization=auth)
    )

    transaction = EosTransaction(
        actions=[
            eosio_token.transfer(from_addr, to_addr, amount, authorization=auth)
        ]
    )
    keys = [EOSKey(private_key)]


```