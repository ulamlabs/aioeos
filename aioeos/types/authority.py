from dataclasses import dataclass, field
from typing import List

from .abi import AbiBytes, BaseAbiObject, UInt16, UInt32, Name


@dataclass
class EosPermissionLevel(BaseAbiObject):
    actor: Name
    permission: Name


@dataclass
class EosKeyWeight(BaseAbiObject):
    key: AbiBytes
    weight: UInt16


@dataclass
class EosPermissionLevelWeight(BaseAbiObject):
    permission: EosPermissionLevel
    weight: UInt16


@dataclass
class EosWaitWeight(BaseAbiObject):
    wait_sec: UInt32
    weight: UInt16


@dataclass
class EosAuthority(BaseAbiObject):
    threshold: UInt32 = 1
    keys: List[EosKeyWeight] = field(default_factory=list)
    accounts: List[EosPermissionLevelWeight] = field(default_factory=list)
    waits: List[EosWaitWeight] = field(default_factory=list)
