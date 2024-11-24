"""Transaction implementation for TalantChain"""

import time
import json
from decimal import Decimal
from typing import Dict, Optional
from ..crypto.hash import Hash
from ..crypto.keys import PrivateKey, PublicKey

class Transaction:
    def __init__(self, sender: str, recipient: str, amount: Decimal,
                 timestamp: Optional[int] = None, signature: Optional[str] = None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = timestamp or int(time.time())
        self.signature = signature
        self._hash = None

    @property
    def hash(self) -> str:
        """Get transaction hash"""
        if not self._hash:
            data = self.to_dict(include_signature=False)
            self._hash = Hash(json.dumps(data, sort_keys=True)).hex()
        return self._hash

    def sign(self, private_key: PrivateKey) -> None:
        """Sign transaction with private key"""
        if self.signature:
            raise ValueError("Transaction already signed")
        
        # Sign transaction hash
        self.signature = private_key.sign(self.hash)

    def verify(self) -> bool:
        """Verify transaction signature"""
        if not self.signature:
            return False
            
        try:
            # Reconstruct public key from sender address
            public_key = PublicKey.from_address(self.sender)
            # Verify signature
            return public_key.verify(self.hash, self.signature)
        except Exception:
            return False

    def to_dict(self, include_signature: bool = True) -> Dict:
        """Convert transaction to dictionary"""
        data = {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': str(self.amount),
            'timestamp': self.timestamp
        }
        if include_signature and self.signature:
            data['signature'] = self.signature
            data['hash'] = self.hash
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Transaction':
        """Create transaction from dictionary"""
        tx = cls(
            sender=data['sender'],
            recipient=data['recipient'],
            amount=Decimal(data['amount']),
            timestamp=data['timestamp']
        )
        if 'signature' in data:
            tx.signature = data['signature']
        return tx

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transaction):
            return NotImplemented
        return self.hash == other.hash
