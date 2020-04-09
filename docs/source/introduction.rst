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

Getting Started
---------------

This guide step-by-step explains how to use aioeos library to submit your first
transaction. Complete example is available at the end of this chapter. Before 
we begin, please make sure you have ``cleos`` utility installed in your system
(part of ``eosio`` package) and that ``aioeos`` is installed.

On macOS::

    $ brew install eosio
    $ pip install aioeos

Running your testnet
^^^^^^^^^^^^^^^^^^^^

Along with the library, we provide an EOS testnet Docker image. Due to `this 
issue <https://github.com/EOSIO/eos/issues/8289>`_ we recommend cloning the 
`eos-testnet <https://github.com/ulamlabs/eos-testnet>`_ repository and running 
``ensure_eosio.sh`` script.

::

    $ git clone https://github.com/ulamlabs/eos-testnet.git
    $ cd eos-testnet
    $ ./ensure_eosio.sh
    # You can check that server is running
    $ cleos get info


Image by default comes with a hardcoded test account:

- Account name: ``eostest12345``
- Private key: ``5JeaxignXEg3mGwvgmwxG6w6wHcRp9ooPw81KjrP2ah6TWSECDN``
- Public key: ``EOS8VhvYTcUMwp9jFD8UWRMPgWsGQoqBfpBvrjjfMCouqRH9JF5qW``

You can parametrize this through env variables, please refer to the `Docker image
README <https://github.com/ulamlabs/eos-testnet/blob/master/README.md>`_.

Let's create another account to send funds to.

::

    # If you don't have a wallet yet, otherwise open it and unlock
    $ cleos wallet create -f ~/.eosio-wallet-pass

    # Import keys for eostest12345 account
    $ cleos wallet import --private-key 5JeaxignXEg3mGwvgmwxG6w6wHcRp9ooPw81KjrP2ah6TWSECDN

    # Create your second account, for example mysecondacc1
    $ cleos system newaccount eostest12345 --transfer mysecondacc1 EOS8VhvYTcUMwp9jFD8UWRMPgWsGQoqBfpBvrjjfMCouqRH9JF5qW --stake-net "1.0000 EOS" --stake-cpu "1.0000 EOS" --buy-ram-kbytes 8192


Submitting your first transaction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's serialize and submit a basic transaction to EOS.io blockchain. We can
think about a transaction as a set of contract calls that we want to execute.
These are called actions. Along with the action itself, we provide a list of
authorizations. These are defined per action. It basically tells the blockchain
which keys will be used to sign this transaction.

Let's say we want to transfer 1.0000 EOS from `eostest12345` to `mysecondacc1`
account.

::

    from aioeos.account import EOSAccount
    from aioeos.contracts import eosio_token
    from aioeos.types import EosTransaction

    test_account = EOSAccount(
        name='eostest12345',
        private_key='5JeaxignXEg3mGwvgmwxG6w6wHcRp9ooPw81KjrP2ah6TWSECDN'
    )

    action = eosio_token.transfer(
        from_addr=test_account.name,
        to_addr='mysecondacc1',
        quantity='1.0000 EOS',
        authorization=[
            test_account.authorization('active')
        ]
    )

Let's also create an instance of `EosJsonRpc`. Remember to always **USE ONLY
NODES THAT YOU TRUST.** Because aioeos doesn't currently support serialization
of action payloads, for this transaction to be ready to be submitted to the
blockchain, we need to ask our RPC node to convert it for us. 

::

    from aioeos.rpc import EosJsonRpc

    rpc = EosJsonRpc(url='http://127.0.0.1:8888')


Now, let's create a transaction containing this action. Each transaction needs
to contain TAPOS fields. These tell the EOS.io blockchain when the transaction
is considered valid, such as the first block in which it can be included, as
well as an expiration date. While we can provide those parameters manually if
we want to, we can also use the RPC to find out the right block number and
prefix. Let's assume that we want these transaction to be valid for next 2
minutes.

::

    from datetime import datetime, timedelta

    block = await rpc.get_head_block()
    transaction = EosTransaction(
        expiration=datetime.now() + timedelta(minutes=2)
        ref_block_num=block['block_num'] & 65535,
        ref_block_prefix=block['ref_block_prefix'],
        actions=[action]
    )

Transaction is now ready to be submitted to the blockchain. It's time to
serialize, sign and push it. An EOS transaction signature is a digest of the
following data:

- Chain ID - identifies the blockchain that transaction is submitted against,
- Transaction,
- 32 context-free bytes - these can be left empty in this case

While we could do it manually, RPC client provides a helper method which does
all of that for us.

::

    response = await rpc.sign_and_push_transaction(
        transaction, keys=[test_account.key]
    )

Example code
^^^^^^^^^^^^

Complete example code::

    import asyncio

    from aioeos.account import EOSAccount
    from aioeos.contracts import eosio_token
    from aioeos.rpc import EosJsonRpc
    from aioeos.types import EosTransaction


    async def example():
        test_account = EOSAccount(
            name='eostest12345',
            private_key='5JeaxignXEg3mGwvgmwxG6w6wHcRp9ooPw81KjrP2ah6TWSECDN'
        )

        action = eosio_token.transfer(
            from_addr=test_account.name,
            to_addr='mysecondacc1',
            quantity='1.0000 EOS',
            authorization=[test_account.authorization('active')]
        )

        rpc = EosJsonRpc(url='http://127.0.0.1:8888')
        block = await rpc.get_head_block()

        transaction = EosTransaction(
            ref_block_num=block['block_num'] & 65535,
            ref_block_prefix=block['ref_block_prefix'],
            actions=[action]
        )

        response = await rpc.sign_and_push_transaction(
            transaction, keys=[test_account.key]
        )
        print(response)


    asyncio.get_event_loop().run_until_complete(example())
