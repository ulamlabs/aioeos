import re
import hashlib
import secrets

import base58
import ecdsa

from aioeos.types import EosKeyWeight


class EosKey:
    """
    EosKey instance.

    Depends on which kwargs are given, this works in a different way:
    - No kwargs - generates a new private key
    - Only private_key - public key is being derived from private key
    - Only public_key - EosKey instance has no private key
    """

    def __init__(self, *, private_key: str = None, public_key: str = None):
        assert not (private_key and public_key), 'Pass only 1 key'
        if private_key:
            private_key = self._parse_key(private_key)
            self._sk = ecdsa.SigningKey.from_string(
                private_key, curve=ecdsa.SECP256k1
            )
        elif not public_key:
            entropy = ecdsa.util.PRNG(secrets.randbits(512))
            self._sk = ecdsa.SigningKey.generate(
                entropy=entropy, curve=ecdsa.SECP256k1
            )
        self._vk = public_key if public_key else self._sk.get_verifying_key()

    def _parse_key(self, private_str):
        """
        EOS has two private key formats.
        - WIF - legacy format, has to start with 0x80 byte,
        - PVT - PVT_{key type}_{base58 encoded key with checksum}
        """
        # check if key is in PVT format
        match = re.search('^PVT_([A-Za-z0-9]+)_([A-Za-z0-9]+)$', private_str)
        if match:
            key_type, key_string = match.groups()
            return self._check_decode(key_string, key_type)

        # fallback to WIF
        private_key = self._check_decode(private_str, 'sha256x2')
        if private_key[0] != 0x80:
            raise ValueError('Invalid version')
        return private_key[1:]

    def _calculate_checksum(self, key, key_type=''):
        """
        Takes a private key, returns a checksum.

        ``key_type`` determines the kind of checksum:
        - sha256x2
        - K1 - rmd160 checksum
        - empty string - rmd160 checksum without suffix
        """
        if key_type == 'sha256x2':
            first_sha = hashlib.sha256(key).digest()
            return hashlib.sha256(first_sha).digest()[:4]
        elif key_type in ('', 'K1'):
            r = hashlib.new('rmd160')
            r.update(key + key_type.encode('utf-8'))
            return r.digest()[:4]
        else:
            raise TypeError('Unsupported key type {}'.format(key_type))

    def _check_encode(self, key_buffer, key_type=''):
        """
        Encodes the key to checksummed base58 format. ``key_type`` determines
        checksum type.
        """
        # base58.b58encode only takes bytes, not bytearray, make sure we have
        # the right type
        assert type(key_buffer) in (bytes, bytearray)
        if isinstance(key_buffer, bytearray):
            key_buffer = bytes(key_buffer)

        checksum = self._calculate_checksum(key_buffer, key_type)

        # b58encode returns bytes, we always cast this to regular strings in
        # a next call so let's do this here
        return base58.b58encode(key_buffer + checksum).decode()

    def _check_decode(self, key_string, key_type=''):
        """
        Decodes the key from checksummed base58 format, checks it against
        expected checksum and returns the value. ``key_type`` determines
        checksum type.
        """
        buffer = base58.b58decode(key_string)
        key, checksum = buffer[:-4], buffer[-4:]
        new_checksum = self._calculate_checksum(key, key_type)

        if checksum != new_checksum:
            raise ValueError(
                f'checksums do not match: {checksum} != {new_checksum}'
            )
        return key

    def _recover_key(self, digest, signature, i):
        ''' Recover the public key from the sig
            http://www.secg.org/sec1-v2.pdf
        '''
        curve = ecdsa.SECP256k1.curve
        G = ecdsa.SECP256k1.generator
        order = ecdsa.SECP256k1.order
        yp = (i % 2)
        r, s = ecdsa.util.sigdecode_string(signature, order)
        x = r + (i // 2) * order
        alpha = ((x * x * x) + (curve.a() * x) + curve.b()) % curve.p()
        beta = ecdsa.numbertheory.square_root_mod_prime(alpha, curve.p())
        y = beta if (beta - yp) % 2 == 0 else curve.p() - beta
        # generate R
        R = ecdsa.ellipticcurve.Point(curve, x, y, order)
        e = ecdsa.util.string_to_number(digest)
        # compute Q
        Q = (
            ecdsa.numbertheory.inverse_mod(r, order)
            * (s * R + (-e % order) * G)
        )
        # verify message
        verifying_key = ecdsa.VerifyingKey.from_public_point(
            Q, curve=ecdsa.SECP256k1
        )
        if not verifying_key.verify_digest(
            signature, digest, sigdecode=ecdsa.util.sigdecode_string
        ):
            return None
        return ecdsa.VerifyingKey.from_public_point(Q, curve=ecdsa.SECP256k1)

    def _recovery_pubkey_param(self, digest, signature):
        """
        Use to derive a number that will allow for the easy recovery of the
        public key from the signature
        """
        for i in range(0, 4):
            p = self._recover_key(digest, signature, i)
            if p.to_string() == self._vk.to_string():
                return i

    def to_public(self):
        """Returns compressed, base58 encoded public key prefixed with EOS"""
        compressed = self._vk.to_string(encoding='compressed')
        return f'EOS{self._check_encode(compressed)}'

    def to_wif(self):
        """Converts private key to legacy WIF format"""
        private_key = b'\x80' + self._sk.to_string()
        return self._check_encode(private_key, 'sha256x2')

    def to_pvt(self, key_type='K1'):
        """Converts private key to PVT format"""
        private_key = self._check_encode(self._sk.to_string(), key_type)
        return f'PVT_{key_type}_{private_key}'

    def sign(self, digest):
        """
        Signs sha256 hash with private key. Returns signature in format:
        ``SIG_K1_{digest}``
        """
        cnt = 0
        if len(digest) != 32:
            raise ValueError("32 byte buffer required")

        # repeat until the signature is canonical
        is_canonical = False
        while not is_canonical:
            # get deterministic k
            sha_digest = hashlib.sha256(
                digest + bytes([cnt] if cnt else [])
            ).digest()

            k = ecdsa.rfc6979.generate_k(
                self._sk.curve.generator.order(),
                self._sk.privkey.secret_multiplier,
                hashlib.sha256,
                sha_digest
            )
            # sign the message, returns der_signature
            der_signature = self._sk.sign_digest(
                digest, sigencode=ecdsa.util.sigencode_der, k=k
            )

            # decode der_signature
            r, s = ecdsa.util.sigdecode_der(
                der_signature, self._sk.curve.generator.order()
            )
            is_canonical = (
                der_signature[3] == 32
                and der_signature[5 + der_signature[3]] == 32
            )
            # try another one if not canonical
            cnt += 1

        # encode signature in string format and derive recovery parameter
        sig = ecdsa.util.sigencode_string(
            r, s, self._sk.curve.generator.order()
        )

        # 4 because it's compressed and 27 because it's compact (?)
        # https://github.com/EOSIO/eosjs-ecc/blob/master/src/signature.js#L216
        i = self._recovery_pubkey_param(digest, sig) + 4 + 27
        return f'SIG_K1_{self._check_encode(bytes([i]) + sig, "K1")}'

    def verify(self, encoded_sig, digest) -> bool:
        """Verifies signature with private key"""
        _, key_type, signature = encoded_sig.split('_')
        try:
            sig = self._check_decode(signature, key_type)[1:]
            self._vk.verify_digest(
                sig, digest, sigdecode=ecdsa.util.sigdecode_string
            )
        except (ecdsa.keys.BadSignatureError, TypeError):
            return False
        return True

    def to_key_weight(self, weight: int) -> EosKeyWeight:
        return EosKeyWeight(key=self.to_public(), weight=weight)

    def __eq__(self, other) -> bool:
        assert isinstance(other, EosKey), 'Can compare only to EosKey instance'
        return self.to_public() == other.to_public()
