from typing import List, Optional, Dict
from .block import Block
from .transaction import Transaction
from ..crypto.hash import Hash
import threading

class Blockchain:
    def __init__(self):
        self.chain: List[Block] = []
        self.current_transactions: List[Transaction] = []
        self.utxo_set: Dict[str, List[int]] = {}  # UTXO set for quick lookups
        self.lock = threading.Lock()
        
        # Create genesis block
        genesis = Block.create_genesis_block()
        self.chain.append(genesis)
    
    @property
    def last_block(self) -> Block:
        return self.chain[-1]
    
    def add_block(self, block: Block) -> bool:
        """Add a new block to the chain"""
        with self.lock:
            # Verify block
            if not self._verify_block(block):
                return False
            
            # Add block to chain
            self.chain.append(block)
            
            # Update UTXO set
            self._update_utxo_set(block)
            
            return True
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """Add a new transaction to the pool"""
        if not self._verify_transaction(transaction):
            return False
            
        with self.lock:
            self.current_transactions.append(transaction)
            return True
    
    def _verify_block(self, block: Block) -> bool:
        """Verify block validity"""
        # Check previous hash
        if block.header.prev_hash != self.last_block.hash:
            return False
        
        # Check block hash meets difficulty
        if not self._check_proof_of_work(block):
            return False
        
        # Verify merkle root
        if block.header.merkle_root != block.calculate_merkle_root():
            return False
        
        # Verify all transactions
        for tx in block.transactions:
            if not self._verify_transaction(tx):
                return False
        
        return True
    
    def _verify_transaction(self, transaction: Transaction) -> bool:
        """Verify transaction validity"""
        # Skip verification for coinbase transactions
        if len(transaction.inputs) == 1 and transaction.inputs[0].prev_tx == Hash():
            return True
        
        # Check that inputs exist and are unspent
        for tx_input in transaction.inputs:
            utxo_key = f"{tx_input.prev_tx}:{tx_input.index}"
            if utxo_key not in self.utxo_set:
                return False
        
        # Verify signatures
        for i, tx_input in enumerate(transaction.inputs):
            if not transaction.verify_signature(i, self._get_output_public_key(tx_input)):
                return False
        
        return True
    
    def _update_utxo_set(self, block: Block) -> None:
        """Update UTXO set with new block"""
        # Remove spent outputs
        for tx in block.transactions:
            for tx_input in tx.inputs:
                utxo_key = f"{tx_input.prev_tx}:{tx_input.index}"
                if utxo_key in self.utxo_set:
                    del self.utxo_set[utxo_key]
        
        # Add new outputs
        for tx in block.transactions:
            tx_hash = tx.hash
            for i, output in enumerate(tx.outputs):
                utxo_key = f"{tx_hash}:{i}"
                self.utxo_set[utxo_key] = output.public_key
    
    def _check_proof_of_work(self, block: Block) -> bool:
        """Check if block meets proof of work requirement"""
        block_hash = block.hash
        target = 2 ** (256 - block.header.difficulty)
        return int.from_bytes(bytes(block_hash), 'big') < target
    
    def _get_output_public_key(self, tx_input: 'TxInput') -> bytes:
        """Get public key from referenced output"""
        utxo_key = f"{tx_input.prev_tx}:{tx_input.index}"
        return self.utxo_set.get(utxo_key, b'')
