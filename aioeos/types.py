from dataclasses import dataclass, field, fields
from typing import List


# EOS ABI types
# TODO: implement bool, uint128, int128, float128, block_timestamp_type,
# symbol, symbol_code, asset, checksum160, checksum256, checksum512,
# public_key, private_key, signature, extended_asset
UInt8 = int
UInt16 = int
UInt32 = int
UInt64 = int
Int8 = int
Int16 = int
Int32 = int
Int64 = int
Float32 = float
Float64 = float
Name = str
String = str
TimePointSec = UInt32
TimePoint = UInt64
AbiBytes = bytes

# this type is weird because it's like int, but it has no fixed size
VarUInt = int


@dataclass
class BaseAbiObject:
    @classmethod
    def _serializable_fields(cls):
        return (x.name for x in fields(cls))


@dataclass
class EosAuthorization(BaseAbiObject):
    actor: Name
    permission: Name


@dataclass
class EosAction(BaseAbiObject):
    account: Name
    name: Name
    authorization: List[EosAuthorization]
    data: AbiBytes


@dataclass
class EosExtension(BaseAbiObject):
    extension_type: UInt16
    data: AbiBytes


@dataclass
class EosTransaction(BaseAbiObject):
    expiration: TimePointSec = None
    ref_block_num: UInt16 = 0
    ref_block_prefix: UInt32 = 0
    max_net_usage_words: VarUInt = 0
    max_cpu_usage_ms: UInt8 = 0
    delay_sec: VarUInt = 0
    context_free_actions: List[EosAction] = field(default_factory=list)
    actions: List[EosAction] = field(default_factory=list)
    transaction_extensions: List[EosExtension] = field(default_factory=list)
