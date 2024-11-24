"""Ring signature implementation for TalantChain"""

from nacl.bindings import crypto_scalarmult_base
from nacl.signing import SigningKey, VerifyKey
from nacl.hash import blake2b
import os
from typing import List, Tuple
from .hash import Hash

class RingSignature:
    @staticmethod
    def generate_key_pair() -> Tuple[bytes, bytes]:
        """Generate a new key pair"""
        private_key = SigningKey.generate()
        public_key = private_key.verify_key
        return private_key.encode(), public_key.encode()
        
    @staticmethod
    def generate_key_image(private_key: bytes, public_key: bytes) -> bytes:
        """Generate key image for ring signature"""
        hp = blake2b(public_key, digest_size=32)
        return crypto_scalarmult_base(hp)
        
    @staticmethod
    def sign(message: bytes, public_keys: List[bytes], private_key: bytes, 
            key_index: int) -> Tuple[List[bytes], bytes]:
        """Create ring signature"""
        n = len(public_keys)
        if key_index >= n:
            raise ValueError("Key index out of range")
            
        # Generate random values
        alpha = os.urandom(32)
        s = [os.urandom(32) for _ in range(n)]
        
        # Calculate key image
        key_image = RingSignature.generate_key_image(private_key, public_keys[key_index])
        
        # Generate c values
        c = [bytes(32) for _ in range(n)]
        h = blake2b(message + key_image, digest_size=32)
        
        # Calculate signature
        for i in range(n):
            if i == key_index:
                continue
            c[(i + 1) % n] = blake2b(h + s[i], digest_size=32)
            
        # Calculate final signature
        s[key_index] = alpha
        for i in range(n):
            if i != key_index:
                s[i] = bytes(x ^ y for x, y in zip(s[i], c[i]))
                
        return s, key_image
        
    @staticmethod
    def verify(message: bytes, public_keys: List[bytes], signature: Tuple[List[bytes], bytes]) -> bool:
        """Verify ring signature"""
        s_values, key_image = signature
        n = len(public_keys)
        
        if len(s_values) != n:
            return False
            
        # Verify key image
        h = blake2b(message + key_image, digest_size=32)
        
        # Calculate and verify c values
        c = [bytes(32) for _ in range(n)]
        for i in range(n):
            c[(i + 1) % n] = blake2b(h + s_values[i], digest_size=32)
            
        # Final verification
        return all(c[i] == blake2b(h + s_values[i], digest_size=32) for i in range(n))
