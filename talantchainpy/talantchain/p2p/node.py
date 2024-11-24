"""Node implementation for TalantChain"""

import asyncio
from typing import Dict, List, Optional, Set
from ..core.block import Block
from ..core.transaction import Transaction
from ..mining.miner import Miner
from decimal import Decimal
import time
import socket

class Node:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.peers: Dict[str, 'Node'] = {}
        self.blockchain = []  # Simplified for this example
        self.mempool: List[Transaction] = []
        self.miner: Optional[Miner] = None
        self.server = None
        self.current_block_height = 0
        self.current_difficulty = 1
        self.is_running = False
        
    async def start(self):
        """Start node server"""
        try:
            self.server = await asyncio.start_server(
                self.handle_connection, self.host, self.port
            )
            self.is_running = True
            
            # If port was 0 (random), get the actual port
            if self.port == 0:
                self.port = self.server.sockets[0].getsockname()[1]
                
            print(f"Node listening on {self.host}:{self.port}")
            
            # Start periodic tasks
            asyncio.create_task(self.update_difficulty())
            asyncio.create_task(self.clean_mempool())
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            print(f"Failed to start node: {e}")
            self.is_running = False
            
    async def stop(self):
        """Stop node server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        self.is_running = False
        
    async def handle_connection(self, reader, writer):
        """Handle incoming peer connection"""
        peer_info = writer.get_extra_info('peername')
        print(f"New connection from {peer_info}")
        
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                    
                # Handle received data
                # This would implement the full P2P protocol
                
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            
    async def connect_to_peer(self, host: str, port: int):
        """Connect to a peer node"""
        try:
            reader, writer = await asyncio.open_connection(host, port)
            peer_id = f"{host}:{port}"
            self.peers[peer_id] = (reader, writer)
            print(f"Connected to peer {peer_id}")
            return True
        except Exception as e:
            print(f"Failed to connect to peer {host}:{port}: {e}")
            return False
            
    def start_mining(self, wallet_address: str):
        """Start mining blocks"""
        if not self.miner:
            self.miner = Miner()
            
        # Initialize mining with current blockchain state
        self.miner.blockchain_height = self.current_block_height
        self.miner.current_difficulty = self.current_difficulty
        self.miner.mempool = self.mempool.copy()
        
        # Start mining
        self.miner.start_mining(wallet_address)
        
    def stop_mining(self):
        """Stop mining blocks"""
        if self.miner:
            self.miner.stop_mining()
            
    async def update_difficulty(self):
        """Periodically update mining difficulty"""
        while self.is_running:
            # Simple difficulty adjustment based on block time
            target_time = 60  # 1 minute per block
            if self.miner and self.miner.last_block_time:
                block_time = time.time() - self.miner.last_block_time
                if block_time < target_time / 2:
                    self.current_difficulty *= 2
                elif block_time > target_time * 2:
                    self.current_difficulty = max(1, self.current_difficulty / 2)
                    
            await asyncio.sleep(60)
            
    async def clean_mempool(self):
        """Periodically clean old transactions from mempool"""
        while self.is_running:
            current_time = time.time()
            self.mempool = [tx for tx in self.mempool 
                          if current_time - tx.timestamp < 3600]  # Remove after 1 hour
            await asyncio.sleep(300)  # Clean every 5 minutes
            
    def add_block(self, block: Block) -> bool:
        """Add a new block to the blockchain"""
        # Verify block
        if self.verify_block(block):
            self.blockchain.append(block)
            self.current_block_height += 1
            
            # Remove block's transactions from mempool
            tx_hashes = {tx.hash for tx in block.transactions}
            self.mempool = [tx for tx in self.mempool if tx.hash not in tx_hashes]
            
            # Update miner's state
            if self.miner:
                self.miner.blockchain_height = self.current_block_height
                self.miner.update_block_template()
                
            return True
        return False
        
    def verify_block(self, block: Block) -> bool:
        """Verify block validity"""
        try:
            # Check block hash meets difficulty
            if not block.meets_difficulty(self.current_difficulty):
                return False
                
            # Verify transactions
            for tx in block.transactions:
                if not tx.verify():
                    return False
                    
            return True
        except Exception:
            return False
