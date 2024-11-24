"""Cryptographic key implementation for TalantChain"""

import os
import base58
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives import serialization
from typing import Tuple
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import HexEncoder
from .hash import Hash

class PrivateKey:
    def __init__(self, key: ec.EllipticCurvePrivateKey):
        self._key = key

    @classmethod
    def generate(cls) -> 'PrivateKey':
        """Generate new private key"""
        key = ec.generate_private_key(ec.SECP256K1())
        return cls(key)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'PrivateKey':
        """Load private key from bytes"""
        key = serialization.load_der_private_key(data, password=None)
        if not isinstance(key, ec.EllipticCurvePrivateKey):
            raise ValueError("Invalid private key type")
        return cls(key)

    def to_bytes(self) -> bytes:
        """Convert private key to bytes"""
        return self._key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

    def get_public_key(self) -> 'PublicKey':
        """Get corresponding public key"""
        return PublicKey(self._key.public_key())

    def sign(self, message: str) -> str:
        """Sign a message"""
        signature = self._key.sign(
            message.encode(),
            ec.ECDSA(hashes.SHA256())
        )
        return base58.b58encode(signature).decode()

class PublicKey:
    def __init__(self, key: ec.EllipticCurvePublicKey):
        self._key = key

    @classmethod
    def from_bytes(cls, data: bytes) -> 'PublicKey':
        """Load public key from bytes"""
        key = serialization.load_der_public_key(data)
        if not isinstance(key, ec.EllipticCurvePublicKey):
            raise ValueError("Invalid public key type")
        return cls(key)

    def to_bytes(self) -> bytes:
        """Convert public key to bytes"""
        return self._key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def to_address(self) -> str:
        """Convert public key to address"""
        # Get the compressed public key bytes
        pub_bytes = self._key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.CompressedPoint
        )
        
        # Double SHA256
        sha256_1 = hashlib.sha256(pub_bytes).digest()
        sha256_2 = hashlib.sha256(sha256_1).digest()
        
        # RIPEMD160
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(sha256_2)
        pub_hash = ripemd160.digest()
        
        # Add version byte (0x00 for mainnet)
        version_hash = b'\x00' + pub_hash
        
        # Double SHA256 for checksum
        checksum = hashlib.sha256(
            hashlib.sha256(version_hash).digest()
        ).digest()[:4]
        
        # Combine and encode to base58
        final_bytes = version_hash + checksum
        return base58.b58encode(final_bytes).decode()

    @classmethod
    def from_address(cls, address: str) -> 'PublicKey':
        """Create public key from address"""
        # This is a dummy implementation since we can't recover the full public key from an address
        # In a real implementation, we would need to store public keys separately
        raise NotImplementedError("Cannot recover public key from address")

    def verify(self, message: str, signature: str) -> bool:
        """Verify a signature"""
        try:
            sig_bytes = base58.b58decode(signature)
            self._key.verify(
                sig_bytes,
                message.encode(),
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception:
            return False

class KeyPair:
    def __init__(self, seed: bytes = None):
        if seed:
            self._signing_key = SigningKey(seed)
        else:
            self._signing_key = SigningKey.generate()
        self._verify_key = self._signing_key.verify_key

    @property
    def private_key(self) -> bytes:
        return bytes(self._signing_key)

    @property
    def public_key(self) -> bytes:
        return bytes(self._verify_key)

    def sign(self, message: bytes) -> bytes:
        return self._signing_key.sign(message).signature

    def verify(self, signature: bytes, message: bytes) -> bool:
        try:
            self._verify_key.verify(message, signature)
            return True
        except:
            return False

    @staticmethod
    def generate_keys() -> Tuple[bytes, bytes]:
        """Generate a new keypair"""
        kp = KeyPair()
        return kp.private_key, kp.public_key

    @staticmethod
    def from_private_key(private_key: bytes) -> 'KeyPair':
        """Create a KeyPair from an existing private key"""
        return KeyPair(private_key)

    def get_address(self) -> str:
        """Generate address from public key"""
        h = Hash(self.public_key)
        return str(h)

def generate_key_pair() -> Tuple[PrivateKey, PublicKey]:
    """Generate new key pair"""
    private_key = PrivateKey.generate()
    public_key = private_key.get_public_key()
    return private_key, public_key
