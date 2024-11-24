"""Node implementation for TalantChain"""

import asyncio
import aiohttp
from aiohttp import web
import json
import time
from decimal import Decimal
from typing import Dict, List, Optional
from ..crypto.hash import Hash
from ..core.transaction import Transaction
from ..database.db import Database

class Node:
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.db = Database()
        self.mempool: List[Transaction] = []
        self.current_block_template = None
        self.current_miners: Dict[str, int] = {}  # address -> last_seen
        self.block_reward = Decimal('50.0')
        self.setup_routes()

    def setup_routes(self):
        """Setup API routes"""
        self.app.router.add_get('/getblocktemplate', self.get_block_template)
        self.app.router.add_post('/submitblock', self.submit_block)
        self.app.router.add_get('/balance/{address}', self.get_balance)
        self.app.router.add_post('/transaction', self.submit_transaction)
        self.app.router.add_get('/info', self.get_info)

    async def get_info(self, request: web.Request) -> web.Response:
        """Get blockchain info"""
        info = {
            'height': self.db.get_height(),
            'difficulty': self.db.get_difficulty(),
            'mempool_size': len(self.mempool),
            'active_miners': len(self.current_miners),
            'block_reward': str(self.block_reward)
        }
        return web.json_response(info)

    async def get_balance(self, request: web.Request) -> web.Response:
        """Get address balance"""
        address = request.match_info['address']
        balance = self.db.get_balance(address)
        return web.json_response({'balance': str(balance)})

    async def submit_transaction(self, request: web.Request) -> web.Response:
        """Submit new transaction"""
        try:
            data = await request.json()
            tx = Transaction.from_dict(data)
            
            # Verify transaction
            if not tx.verify():
                return web.Response(status=400, text="Invalid transaction signature")
                
            # Check sender has enough balance
            balance = self.db.get_balance(tx.sender)
            if balance < tx.amount:
                return web.Response(status=400, text="Insufficient balance")
                
            # Add to mempool
            self.mempool.append(tx)
            return web.Response(status=200)
            
        except Exception as e:
            return web.Response(status=400, text=str(e))

    def create_block_template(self, miner_address: str) -> dict:
        """Create new block template"""
        height = self.db.get_height() + 1
        prev_hash = self.db.get_latest_block_hash()
        timestamp = int(time.time())
        difficulty = self.db.get_difficulty()
        
        # Get transactions from mempool
        transactions = self.mempool[:10]  # Limit to 10 transactions per block
        
        template = {
            'height': height,
            'previous_hash': prev_hash,
            'timestamp': timestamp,
            'difficulty': difficulty,
            'transactions': [tx.to_dict() for tx in transactions],
            'miner_address': miner_address,
            'reward': str(self.block_reward)
        }
        
        return template

    async def get_block_template(self, request: web.Request) -> web.Response:
        """Get block template for mining"""
        try:
            params = request.rel_url.query
            miner_address = params.get('address')
            if not miner_address:
                return web.Response(status=400, text="Miner address required")
                
            # Update miner's last seen time
            self.current_miners[miner_address] = int(time.time())
            
            # Create new template
            template = self.create_block_template(miner_address)
            return web.json_response(template)
            
        except Exception as e:
            return web.Response(status=400, text=str(e))

    async def submit_block(self, request: web.Request) -> web.Response:
        """Submit mined block"""
        try:
            block_data = await request.json()
            
            # Verify block hash meets difficulty
            block_hash = Hash(json.dumps(block_data, sort_keys=True))._bytes
            hash_int = int.from_bytes(block_hash, byteorder='big')
            target = 2 ** (256 - block_data['difficulty'])
            
            if hash_int >= target:
                return web.Response(status=400, text="Block hash does not meet difficulty")
                
            # Process block reward
            miner_address = block_data['miner_address']
            self.db.add_balance(miner_address, self.block_reward)
            
            # Process transactions
            for tx_data in block_data['transactions']:
                tx = Transaction.from_dict(tx_data)
                # Deduct from sender
                self.db.subtract_balance(tx.sender, tx.amount)
                # Add to recipient
                self.db.add_balance(tx.recipient, tx.amount)
                # Remove from mempool
                self.mempool = [t for t in self.mempool if t.hash != tx.hash]
                
            # Save block
            self.db.add_block(block_data)
            
            # Update difficulty if needed
            self.adjust_difficulty()
            
            return web.Response(status=200)
            
        except Exception as e:
            return web.Response(status=400, text=str(e))

    def adjust_difficulty(self):
        """Adjust mining difficulty based on block time"""
        # Get last 10 blocks
        blocks = self.db.get_last_n_blocks(10)
        if len(blocks) < 2:
            return
            
        # Calculate average block time
        times = [b['timestamp'] for b in blocks]
        avg_time = (times[-1] - times[0]) / (len(times) - 1)
        
        # Target block time is 60 seconds
        if avg_time < 30:  # Too fast
            self.db.increase_difficulty()
        elif avg_time > 90:  # Too slow
            self.db.decrease_difficulty()

    async def start(self):
        """Start node"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        print(f"Starting node on {self.host}:{self.port}")
        await site.start()
        
        # Start background tasks
        asyncio.create_task(self.cleanup_old_miners())
        
        # Keep server running
        while True:
            await asyncio.sleep(1)

    async def stop(self):
        """Stop node"""
        await self.app.shutdown()

    async def cleanup_old_miners(self):
        """Remove inactive miners"""
        while True:
            current_time = int(time.time())
            self.current_miners = {
                addr: last_seen 
                for addr, last_seen in self.current_miners.items()
                if current_time - last_seen < 300  # 5 minutes timeout
            }
            await asyncio.sleep(60)  # Check every minute
