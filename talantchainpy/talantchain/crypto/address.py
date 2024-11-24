"""Address generation for TalantChain"""

import os
import hashlib
import base58
from typing import Tuple

class Address:
    PREFIX = b'TLNT'  # TalantChain prefix
    ADDRESS_LENGTH = 95  # Similar to Monero

    @staticmethod
    def create_address() -> Tuple[str, bytes, bytes]:
        """Create new address with spend and view keys"""
        # Generate random 32-byte private spend key
        spend_key = os.urandom(32)
        
        # Generate random 32-byte private view key
        view_key = os.urandom(32)
        
        # Generate public keys using Keccak-256
        spend_public = Address._get_public_key(spend_key)
        view_public = Address._get_public_key(view_key)
        
        # Create address from public keys
        address = Address._public_keys_to_address(spend_public, view_public)
        
        return address, spend_key, view_key

    @staticmethod
    def _get_public_key(private_key: bytes) -> bytes:
        """Generate public key from private key using Keccak"""
        keccak = hashlib.sha3_256()
        keccak.update(private_key)
        return keccak.digest()

    @staticmethod
    def _public_keys_to_address(spend_public: bytes, view_public: bytes) -> str:
        """Convert public keys to address string"""
        # Concatenate data
        data = Address.PREFIX + spend_public + view_public
        
        # Calculate checksum (first 4 bytes of double Keccak)
        keccak = hashlib.sha3_256()
        keccak.update(data)
        first_hash = keccak.digest()
        
        keccak = hashlib.sha3_256()
        keccak.update(first_hash)
        checksum = keccak.digest()[:4]
        
        # Final binary address
        binary_address = data + checksum
        
        # Encode to base58
        address = base58.b58encode(binary_address).decode()
        
        return address

    @staticmethod
    def is_valid_address(address: str) -> bool:
        """Verify if address is valid"""
        try:
            # Decode from base58
            data = base58.b58decode(address.encode())
            
            # Check length
            if len(data) != len(Address.PREFIX) + 32 + 32 + 4:  # prefix + spend + view + checksum
                return False
                
            # Check prefix
            if data[:len(Address.PREFIX)] != Address.PREFIX:
                return False
                
            # Check checksum
            checksum = data[-4:]
            main_data = data[:-4]
            
            # Calculate checksum
            keccak = hashlib.sha3_256()
            keccak.update(main_data)
            first_hash = keccak.digest()
            
            keccak = hashlib.sha3_256()
            keccak.update(first_hash)
            calculated_checksum = keccak.digest()[:4]
            
            return checksum == calculated_checksum
            
        except Exception:
            return False

    @staticmethod
    def get_public_keys(address: str) -> Tuple[bytes, bytes]:
        """Extract public keys from address"""
        try:
            data = base58.b58decode(address.encode())
            prefix_len = len(Address.PREFIX)
            spend_public = data[prefix_len:prefix_len + 32]
            view_public = data[prefix_len + 32:prefix_len + 64]
            return spend_public, view_public
        except Exception:
            raise ValueError("Invalid address")
