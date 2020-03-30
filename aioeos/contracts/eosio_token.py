"""Wrapper for creating actions on eosio.token contract"""
from aioeos.types import EosAction


def transfer(
    from_addr, to_addr, quantity, memo='', authorization=[]
) -> EosAction:
    return EosAction(
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


def close(owner, symbol, authorization=[]) -> EosAction:
    return EosAction(
        account='eosio.token',
        name='close',
        authorization=authorization,
        data={
            'owner': owner,
            'symbol': symbol
        }
    )
