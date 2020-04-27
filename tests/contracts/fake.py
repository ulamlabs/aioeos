"""
Fake, typed out contract for testing purposes
"""
from dataclasses import dataclass

from aioeos.types import BaseAbiObject, EosAction, UInt8


@dataclass
class Payload(BaseAbiObject):
    a: UInt8


account = 'eosio.fake'
name = 'test'
abi = {
    'version': 'eosio::abi/1.0',
    'structs': [
        {
            'name': name,
            'base': '',
            'fields': [
                {
                    'name': 'a',
                    'type': 'int8'
                }
            ]
        }
    ],
    'actions': [
        {
            'name': name,
            'type': name,
            'ricardian_contract': ''
        }
    ]
}


def test(a: int, authorization=[]) -> EosAction:
    return EosAction(
        account=account,
        name=name,
        authorization=authorization,
        data=Payload(a=a)
    )
