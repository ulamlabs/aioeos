from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import Any, ClassVar, Dict, List, NewType, TYPE_CHECKING, Union


# EOS ABI types
# TODO: implement bool, uint128, int128, float128, block_timestamp_type,
# symbol, symbol_code, asset, checksum160, checksum256, checksum512,
# public_key, private_key, signature, extended_asset
if TYPE_CHECKING:
    UInt8 = int
    UInt16 = int
    UInt32 = int
    UInt64 = int
    Int8 = int
    Int16 = int
    Int32 = int
    Int64 = int
    VarUInt = int
    Float32 = float
    Float64 = float
    TimePointSec = datetime
    TimePoint = datetime
    Name = str
    AbiBytes = bytes
else:
    # Our runtime logic depends on these being new types, but this makes mypy
    # require explicit casting
    UInt8 = NewType('UInt8', int)
    UInt16 = NewType('UInt16', int)
    UInt32 = NewType('UInt32', int)
    UInt64 = NewType('UInt64', int)
    Int8 = NewType('Int8', int)
    Int16 = NewType('Int16', int)
    Int32 = NewType('Int32', int)
    Int64 = NewType('Int64', int)
    Float32 = NewType('Float32', float)
    Float64 = NewType('Float64', float)
    Name = NewType('Name', str)
    TimePointSec = NewType('TimePointSec', datetime)
    TimePoint = NewType('TimePoint', datetime)
    AbiBytes = NewType('AbiBytes', bytes)

    # this type is weird because it's like int, but it has no fixed size
    VarUInt = NewType('VarUInt', int)

AbiActionPayload = Union[Dict[str, Any], AbiBytes]


@dataclass
class BaseAbiObject:
    __dataclass_fields__: ClassVar[Dict]

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
    data: AbiActionPayload


@dataclass
class EosExtension(BaseAbiObject):
    extension_type: UInt16
    data: AbiBytes


@dataclass
class EosTransaction(BaseAbiObject):
    expiration: TimePointSec = field(default_factory=datetime.now)
    ref_block_num: UInt16 = UInt16(0)
    ref_block_prefix: UInt32 = 0
    max_net_usage_words: VarUInt = 0
    max_cpu_usage_ms: UInt8 = 0
    delay_sec: VarUInt = 0
    context_free_actions: List[EosAction] = field(default_factory=list)
    actions: List[EosAction] = field(default_factory=list)
    transaction_extensions: List[EosExtension] = field(default_factory=list)
