Introduction
============

aioeos is an ssync Python library for interacting with EOS.io blockchain.
Library consists of an async wrapper for `Nodeos RPC API 
<https://developers.eos.io/eosio-nodeos/docs>`_, a serializer for basic
ABI types like transactions and actions and private key management. Helpers for
generating actions such as creating new accounts, buying and selling RAM etc.
can be imported from `aioeos.contracts` namespace.

Please bear in mind that the serializer is not complete. Action payloads need
to be converted to binary format using `/abi_json_to_bin` endpoint on the RPC
node. Use only nodes you trust.

Features
--------

1. Async JSON-RPC client.
2. Signing and verifying transactions using private and public keys.
3. Serializer for basic EOS.io blockchain ABI types.
4. Helpers which provide an easy way to generate common actions, such as token
   transfer.

Missing features
----------------

1. Serializer and deserializer for action payloads.
2. Support for types:

   - bool,
   - uint128,
   - int128,
   - float128,
   - block_timestamp_type,
   - symbol,
   - symbol_code,
   - asset,
   - checksum160,
   - checksum256,
   - checksum512,
   - public_key,
   - private_key,
   - signature,
   - extended_asset

Submitting your first transaction
---------------------------------

Let's serialize and submit a basic transaction to EOS.io blockchain. We can
think about a transaction as a set of contract calls that we want to execute.
These are called actions. Along with the action itself, we provide a list of
authorizations. These are defined per action. It basically tells the blockchain
which keys will be used to sign this transaction.

Let's say we want to transfer 1.0000 EOS from `myaddress` to `ulamlabscoin`
account.

::

    from aioeos.contracts import eosio_token
    from aioeos.types import EosAuthorization, EosTransaction

    action = eosio_token.transfer(
        from_addr='myaddress',
        to_addr='ulamlabscoin',
        quantity='1.0000 EOS',
        authorization=[
            EosAuthorization(actor='myaddress', permission='active')
        ]
    )

Because aioeos doesn't currently support serialization of action payloads, for
this transaction to be ready to be submitted to the blockchain, we need to ask
our RPC node to convert it for us. Remember to always **USE ONLY NODES THAT YOU
TRUST.**

::

    import binascii
    from aioeos.rpc import EosJsonRpc

    rpc = EosJsonRpc()
    abi_bin = await rpc.abi_json_to_bin(
        action.account, action.name, action.data
    )
    action.data = binascii.unhexlify(abi_bin['binargs'])


Now, let's create a transaction containing this action. Each transaction needs
to contain TAPOS fields. These tell the EOS.io blockchain when the transaction
is considered valid, such as the first block in which it can be included, as
well as an expiration date. While we can provide those parameters manually if
we want to, we can also use the RPC to find out the right block number and
prefix. Let's assume that we want these transaction to be valid since current
block, for 2 minutes after it was mined.

::

    from datetime import datetime, timedelta
    import pytz

    info = await rpc.get_info()
    block = await rpc.get_block(info['head_block_num'])

    expiration = datetime.fromisoformat(block['timestamp']).replace(tzinfo=pytz.UTC)
    expiration += timedelta(seconds=120)

    transaction = EosTransaction(
        expiration=expiration,
        ref_block_num=block['block_num'] & 65535,
        ref_block_prefix=block['ref_block_prefix'],
        actions=[action]
    )

Transaction is now ready to be submitted to the blockchain. It's time to
serialize, sign and push it. An EOS transaction signature is a digest of the
following data:

- Chain ID,
- Transaction,
- 32 context-free bytes 

While we can hardcode the first one, let's use the data we already got from RPC.
Context-free bytes can be left empty. 

::

    import hashlib
    from aioeos.serializer import serialize

    chain_id = info.get('chain_id')
    serialized_transaction = serialize(transaction)
    context_free_bytes = bytes(32)

    digest = (
        hashlib.sha256(
            b''.join(
                binascii.unhexlify(chain_id),
                serialized_transaction,
                context_free_bytes
            )
        ).digest()
    )

For signing, we're going to use EOSKey class. You can initialize it with your
private key, public key (if you want to simply verify a signature) or just
leave it empty. By default, a new signing key will be generated.

::

    from aioeos.keys import EOSKey

    key = EOSKey(private_key=my_private_key)
    signature = key.sign(digest)

A signed and serialized transaction can be now submitted to the blockchain::

    response = await rpc.push_transaction(
        signatures=[signature],
        serialized_transaction=binascii.hexlify(serialized_transaction).decode()
    )
