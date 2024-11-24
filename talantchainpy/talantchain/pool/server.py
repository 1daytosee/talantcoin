"""Pool server implementation for TalantChain"""

import asyncio
import aiohttp
import json
import time
from decimal import Decimal
from typing import Dict, List, Optional
from aiohttp import web
import logging
import base64
from ..crypto.hash import Hash
from ..mining.miner import RandomXLite, Block

class PoolWorker:
    def __init__(self, address: str, worker_name: str):
        self.address = address
        self.worker_name = worker_name
        self.shares = 0
        self.invalid_shares = 0
        self.last_share = 0
        self.hashrate = 0.0
        self.total_paid = Decimal('0')

class MiningPool:
    def __init__(self, pool_address: str, fee: float = 0.01, min_payout: Decimal = Decimal('1.0')):
        self.pool_address = pool_address
        self.fee = fee  # 1% default fee
        self.min_payout = min_payout
        self.workers: Dict[str, PoolWorker] = {}
        self.current_block: Optional[Block] = None
        self.shares_this_round = 0
        self.total_shares = 0
        self.total_blocks_found = 0
        self.total_rewards = Decimal('0')
        self.pending_payments: Dict[str, Decimal] = {}
        self.randomx = RandomXLite()
        self.node_url = "http://localhost:8080"
        self.last_block_time = time.time()
        self.target_time = 60  # 60 seconds per block

    async def start(self):
        """Start pool operations"""
        asyncio.create_task(self._update_block_template())
        asyncio.create_task(self._process_payments())

    async def _update_block_template(self):
        """Continuously update block template"""
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get(
                        f"{self.node_url}/getblocktemplate",
                        params={'address': self.pool_address}
                    ) as response:
                        if response.status == 200:
                            template = await response.json()
                            self.current_block = Block.from_dict(template)
                except Exception as e:
                    logging.error(f"Error updating block template: {e}")
                await asyncio.sleep(1)

    async def submit_share(self, worker_address: str, worker_name: str, nonce: int, hash_result: str) -> bool:
        """Process submitted share from worker"""
        if not self.current_block:
            return False

        # Register worker if new
        worker_key = f"{worker_address}_{worker_name}"
        if worker_key not in self.workers:
            self.workers[worker_key] = PoolWorker(worker_address, worker_name)

        worker = self.workers[worker_key]
        
        # Verify share
        self.current_block.nonce = nonce
        block_hash = self.current_block.hash(self.randomx)
        
        if block_hash.hex() != hash_result:
            worker.invalid_shares += 1
            return False

        # Update worker stats
        worker.shares += 1
        worker.last_share = time.time()
        self.shares_this_round += 1
        self.total_shares += 1

        # Check if block found
        if self.current_block.meets_difficulty(block_hash, self.current_block.difficulty):
            if time.time() - self.last_block_time >= self.target_time:
                await self._handle_block_found(self.current_block)

        return True

    async def _handle_block_found(self, block: Block):
        """Handle found block and distribute rewards"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.node_url}/submitblock",
                    json=block.to_dict()
                ) as response:
                    if response.status == 200:
                        self.total_blocks_found += 1
                        reward = block.reward
                        self.total_rewards += reward
                        
                        # Calculate rewards
                        pool_fee = reward * Decimal(str(self.fee))
                        miner_reward = reward - pool_fee

                        # Distribute rewards based on shares
                        for worker in self.workers.values():
                            if worker.shares > 0:
                                share_percent = worker.shares / self.shares_this_round
                                worker_reward = miner_reward * Decimal(str(share_percent))
                                self.pending_payments[worker.address] = (
                                    self.pending_payments.get(worker.address, Decimal('0')) + 
                                    worker_reward
                                )

                        # Reset round
                        self.shares_this_round = 0
                        self.last_block_time = time.time()
                        
                        logging.info(f"Block found! Height: {block.height}, Reward: {reward} TLNT")
            except Exception as e:
                logging.error(f"Error submitting block: {e}")

    async def _process_payments(self):
        """Process pending payments to miners"""
        while True:
            try:
                for address, amount in list(self.pending_payments.items()):
                    if amount >= self.min_payout:
                        # Send payment
                        async with aiohttp.ClientSession() as session:
                            payment_data = {
                                'from_address': self.pool_address,
                                'to_address': address,
                                'amount': str(amount)
                            }
                            async with session.post(
                                f"{self.node_url}/sendtransaction",
                                json=payment_data
                            ) as response:
                                if response.status == 200:
                                    # Update worker stats
                                    for worker in self.workers.values():
                                        if worker.address == address:
                                            worker.total_paid += amount
                                    # Clear pending payment
                                    self.pending_payments[address] = Decimal('0')
                                    logging.info(f"Payment sent to {address}: {amount} TLNT")
            except Exception as e:
                logging.error(f"Error processing payments: {e}")
            await asyncio.sleep(60)  # Check payments every minute

    def get_stats(self) -> dict:
        """Get pool statistics"""
        total_hashrate = sum(w.hashrate for w in self.workers.values())
        active_workers = sum(1 for w in self.workers.values() 
                           if time.time() - w.last_share < 600)  # Active in last 10 minutes
        
        return {
            'total_hashrate': total_hashrate,
            'active_workers': active_workers,
            'total_workers': len(self.workers),
            'total_shares': self.total_shares,
            'shares_this_round': self.shares_this_round,
            'total_blocks_found': self.total_blocks_found,
            'total_rewards': str(self.total_rewards),
            'fee': self.fee,
            'min_payout': str(self.min_payout)
        }

    def get_worker_stats(self, address: str) -> List[dict]:
        """Get statistics for all workers of an address"""
        worker_stats = []
        for worker in self.workers.values():
            if worker.address == address:
                worker_stats.append({
                    'worker_name': worker.worker_name,
                    'shares': worker.shares,
                    'invalid_shares': worker.invalid_shares,
                    'hashrate': worker.hashrate,
                    'total_paid': str(worker.total_paid),
                    'pending_payment': str(self.pending_payments.get(address, Decimal('0')))
                })
        return worker_stats
