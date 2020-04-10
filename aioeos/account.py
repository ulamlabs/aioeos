from typing import Optional

from aioeos.keys import EosKey
from aioeos.types import EosPermissionLevel, EosPermissionLevelWeight


class EosAccount:
    """
    Describes account on EOS blockchain. Contrary to other blockchains such as
    Bitcoin or Ethereum, public key is not an address. An account can have
    multiple keys with certain permissions, the default ones are "active" and
    "owner". These keys are specified in the transaction which creates the
    account in the first place.

    Class provides a set of helper methods for generating objects such as
    authorizations.

    :param name: name of the account,

    Please provide key in one of the formats - EosKey instance, private key in
    WIF or PVT format and public key. Only one of these is accepted. If no key
    is provided, a new one will be generated.

    ;param key: EosKey instance,
    :param private_key: private key in WIF or PVT format,
    :param public_key: public key
    """

    def __init__(
        self,
        name: str,
        *,
        key: Optional[EosKey] = None,
        private_key: str = '',
        public_key: str = '',
    ):
        assert name, "Account name can't be empty"

        # While this could be written as some kind of binary operation and it
        # would be clever and cool, this is more clear
        assert any((
            key and not private_key and not public_key,
            not key and private_key and not public_key,
            not key and not private_key and public_key,
            not key and not private_key and not public_key
        )), 'Exactly 1 key is required'

        self.name = name
        self.key = (
            key or EosKey(public_key=public_key, private_key=private_key)
        )

    def authorization(self, permission: str) -> EosPermissionLevel:
        """Creates authorization object with given permission"""
        return EosPermissionLevel(actor=self.name, permission=permission)

    def permission_level_weight(
        self, permission: str, weight: int
    ) -> EosPermissionLevelWeight:
        return EosPermissionLevelWeight(
            permission=self.authorization(permission),
            weight=weight
        )
