from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict
from ..crypto.hash import Hash
from .transaction import Transaction

@dataclass
class BlockHeader:
    version: int
    prev_hash: Hash
    merkle_root: Hash
    timestamp: int
    difficulty: int
    nonce: int

    def serialize(self) -> bytes:
        """Serialize the block header"""
        return (
            self.version.to_bytes(4, 'little') +
            bytes(self.prev_hash) +
            bytes(self.merkle_root) +
            self.timestamp.to_bytes(8, 'little') +
            self.difficulty.to_bytes(4, 'little') +
            self.nonce.to_bytes(4, 'little')
        )

@dataclass
class Block:
    header: BlockHeader
    transactions: List[Transaction]

    @property
    def hash(self) -> Hash:
        return self.calculate_hash()

    @property
    def timestamp(self) -> int:
        """Get block timestamp"""
        return self.header.timestamp

    def calculate_hash(self) -> Hash:
        """Calculate block hash"""
        return Hash(self.header.serialize())

    def calculate_merkle_root(self) -> Hash:
        """Calculate merkle root of transactions"""
        if not self.transactions:
            return Hash()
        
        hashes = [tx.hash for tx in self.transactions]
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])
            hashes = [Hash(bytes(h1) + bytes(h2)) 
                     for h1, h2 in zip(hashes[::2], hashes[1::2])]
        return hashes[0]
    
    @classmethod
    def create_genesis_block(cls) -> 'Block':
        """Create the genesis block"""
        header = BlockHeader(
            version=1,
            prev_hash=Hash(),  # Zero hash for genesis block
            merkle_root=Hash(),
            timestamp=int(datetime.now().timestamp()),
            difficulty=1,
            nonce=0
        )
        return cls(header=header, transactions=[])
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Block':
        """Create block from dictionary"""
        header = BlockHeader(
            version=data['header']['version'],
            prev_hash=Hash.from_hex(data['header']['prev_hash']),
            merkle_root=Hash.from_hex(data['header']['merkle_root']),
            timestamp=data['header']['timestamp'],
            difficulty=data['header']['difficulty'],
            nonce=data['header']['nonce']
        )
        
        transactions = [Transaction.from_dict(tx) for tx in data.get('transactions', [])]
        block = cls(header=header, transactions=transactions)
        
        # Verify block hash if provided
        if 'hash' in data and block.hash.hex() != data['hash']:
            raise ValueError("Block hash mismatch")
            
        return block
    
    def to_dict(self) -> Dict:
        """Convert block to dictionary"""
        return {
            'hash': self.hash.hex(),
            'header': {
                'version': self.header.version,
                'prev_hash': self.header.prev_hash.hex(),
                'merkle_root': self.header.merkle_root.hex(),
                'timestamp': self.header.timestamp,
                'difficulty': self.header.difficulty,
                'nonce': self.header.nonce
            },
            'transactions': [tx.to_dict() for tx in self.transactions]
        }
    
    def meets_difficulty(self, difficulty: int) -> bool:
        """Check if block hash meets difficulty target"""
        target = 2 ** (256 - difficulty)
        return int.from_bytes(bytes(self.hash), 'big') < target

    def verify(self) -> bool:
        """Verify block validity"""
        # Verify merkle root
        if self.header.merkle_root != self.calculate_merkle_root():
            return False
        
        # Verify proof of work
        target = 2 ** (256 - self.header.difficulty)
        if int.from_bytes(bytes(self.hash), 'big') >= target:
            return False
        
        # Verify transactions
        return all(tx.verify() for tx in self.transactions)
