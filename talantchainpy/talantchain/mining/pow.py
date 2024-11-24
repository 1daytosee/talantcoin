import time
from typing import List, Optional
from ..core.block import Block, BlockHeader
from ..core.transaction import Transaction
from ..crypto.hash import Hash

class ProofOfWork:
    def __init__(self, initial_difficulty: int = 1):
        self.difficulty = initial_difficulty
        self.target_block_time = 60  # Target 1 block per minute
    
    def mine_block(self, prev_hash: Hash, transactions: List[Transaction]) -> Optional[Block]:
        """Mine a new block"""
        # Create block header
        header = BlockHeader(
            version=1,
            prev_hash=prev_hash,
            merkle_root=Hash(),  # Temporary, will be calculated
            timestamp=int(time.time()),
            difficulty=self.difficulty,
            nonce=0
        )
        
        # Create block
        block = Block(header=header, transactions=transactions)
        
        # Calculate merkle root
        block.header.merkle_root = block.calculate_merkle_root()
        
        # Mine block
        target = 2 ** (256 - self.difficulty)
        max_nonce = 2 ** 32  # 4 billion
        
        start_time = time.time()
        for nonce in range(max_nonce):
            block.header.nonce = nonce
            block_hash = block.calculate_hash()
            
            if int.from_bytes(bytes(block_hash), 'big') < target:
                print(f"Block mined! Nonce: {nonce}, Hash: {block_hash.hex()}")
                return block
            
            # Print progress every million attempts
            if nonce % 1_000_000 == 0:
                elapsed = time.time() - start_time
                print(f"Mining... Tried {nonce:,} hashes ({nonce/elapsed:,.0f} h/s)")
        
        return None
    
    def verify_pow(self, block: Block) -> bool:
        """Verify proof of work for a block"""
        target = 2 ** (256 - block.header.difficulty)
        return int.from_bytes(bytes(block.hash), 'big') < target
    
    def adjust_difficulty(self, last_block_time: int, current_time: int):
        """Adjust mining difficulty based on block time"""
        block_time = current_time - last_block_time
        
        # Adjust difficulty to target one block per minute
        if block_time < self.target_block_time / 2:
            self.difficulty += 1
            print(f"Mining too fast. Increasing difficulty to {self.difficulty}")
        elif block_time > self.target_block_time * 2:
            self.difficulty = max(1, self.difficulty - 1)
            print(f"Mining too slow. Decreasing difficulty to {self.difficulty}")
        
        print(f"Block time: {block_time}s, Target: {self.target_block_time}s, Difficulty: {self.difficulty}")
