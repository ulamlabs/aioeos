from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Union

from .abi import (
    AbiBytes, BaseAbiObject, UInt8, UInt16, UInt32, VarUInt, Name, TimePointSec
)
from .authority import EosPermissionLevel


AbiActionPayload = Union[Dict[str, Any], AbiBytes, BaseAbiObject]


@dataclass
class EosAction(BaseAbiObject):
    account: Name
    name: Name
    authorization: List[EosPermissionLevel]
    data: AbiActionPayload


@dataclass
class EosExtension(BaseAbiObject):
    extension_type: UInt16
    data: AbiBytes


@dataclass
class EosTransaction(BaseAbiObject):
    # TAPOS fields
    expiration: TimePointSec = field(
        default_factory=lambda: datetime.now() + timedelta(seconds=120)
    )
    ref_block_num: UInt16 = 0
    ref_block_prefix: UInt32 = 0

    max_net_usage_words: VarUInt = 0
    max_cpu_usage_ms: UInt8 = 0
    delay_sec: VarUInt = 0
    context_free_actions: List[EosAction] = field(default_factory=list)
    actions: List[EosAction] = field(default_factory=list)
    transaction_extensions: List[EosExtension] = field(default_factory=list)
