"""Helpers for creating actions on eosio.token contract"""
from aioeos import types


def transfer(
    from_addr: str,
    to_addr: str,
    quantity: str,
    memo: str = '',
    authorization=[]
) -> types.EosAction:
    return types.EosAction(
        account='eosio.token',
        name='transfer',
        authorization=authorization,
        data={
            'from': from_addr,
            'to': to_addr,
            'quantity': quantity,
            'memo': memo
        }
    )


def close(owner, symbol, authorization=[]) -> types.EosAction:
    return types.EosAction(
        account='eosio.token',
        name='close',
        authorization=authorization,
        data={
            'owner': owner,
            'symbol': symbol
        }
    )
