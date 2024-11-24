from typing import Union
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base58

class Hash:
    SIZE = 32  # 256 bits

    def __init__(self, data: Union[bytes, str, None] = None):
        self._bytes = bytes(self.SIZE) if data is None else self._hash(data)

    @staticmethod
    def _hash(data: Union[bytes, str]) -> bytes:
        if isinstance(data, str):
            data = data.encode()
        digest = hashes.Hash(hashes.SHA3_256())
        digest.update(data)
        return digest.finalize()

    def __bytes__(self) -> bytes:
        return self._bytes

    def __str__(self) -> str:
        return base58.b58encode(self._bytes).decode('utf-8')
        
    def hex(self) -> str:
        """Return hexadecimal string representation"""
        return self._bytes.hex()

    @staticmethod
    def from_string(s: str) -> 'Hash':
        h = Hash()
        h._bytes = base58.b58decode(s)
        return h
        
    @staticmethod
    def from_hex(s: str) -> 'Hash':
        """Create Hash from hex string"""
        h = Hash()
        h._bytes = bytes.fromhex(s)
        return h

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hash):
            return NotImplemented
        return self._bytes == other._bytes

    def __hash__(self) -> int:
        return hash(self._bytes)

    @staticmethod
    def cn_fast_hash(data: Union[bytes, str]) -> 'Hash':
        """CryptoNight fast hash implementation"""
        h = Hash(data)
        # Note: In a real implementation, we would use the actual CryptoNight algorithm
        return h
