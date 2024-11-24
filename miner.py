#!/usr/bin/env python3

import os
import sys
import json
import time
import hashlib
import logging
import asyncio
import aiohttp
import argparse
import platform
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class MinerT1:
    def __init__(self, pool_url, wallet_address, worker_name=None, threads=None, use_tor=False):
        self.pool_url = pool_url
        self.wallet_address = wallet_address
        self.worker_name = worker_name or f"minert1_{platform.node()}_{os.getpid()}"
        self.threads = threads or max(1, os.cpu_count() - 1)
        self.use_tor = use_tor
        self.running = False
        self.shares_submitted = 0
        self.shares_accepted = 0
        self.start_time = time.time()
        self.hashrate = 0
        self.session = None
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger('MinerT1')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    async def _init_session(self):
        if self.use_tor:
            connector = aiohttp.TCPConnector(
                ssl=False,
                proxy="socks5://127.0.0.1:9050"
            )
        else:
            connector = aiohttp.TCPConnector(ssl=False)
        
        self.session = aiohttp.ClientSession(connector=connector)

    def _calculate_hash(self, data, nonce):
        """CPU-optimized hashing function"""
        data_with_nonce = f"{data}{nonce}".encode()
        # Multiple rounds of hashing for memory-hardness
        h = hashlib.sha256(data_with_nonce).digest()
        for _ in range(10):  # Memory-hard iterations
            h = hashlib.sha256(h).digest()
        return h.hex()

    async def _get_work(self):
        """Get work from pool"""
        try:
            async with self.session.get(f"{self.pool_url}/getwork") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"Failed to get work: {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Error getting work: {e}")
            return None

    async def _submit_share(self, work_id, nonce, hash_result):
        """Submit share to pool"""
        data = {
            "work_id": work_id,
            "nonce": nonce,
            "hash": hash_result,
            "worker": self.worker_name,
            "wallet": self.wallet_address
        }
        
        try:
            async with self.session.post(
                f"{self.pool_url}/submit",
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("accepted", False):
                        self.shares_accepted += 1
                    self.shares_submitted += 1
                    return result
                else:
                    self.logger.error(f"Share submission failed: {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Error submitting share: {e}")
            return None

    def _mining_thread(self, thread_id, work_data):
        """Mining thread function"""
        start_nonce = thread_id * 100000000
        max_nonce = start_nonce + 100000000
        target = work_data["target"]
        data = work_data["data"]
        hashes = 0
        start_time = time.time()

        for nonce in range(start_nonce, max_nonce):
            if not self.running:
                break

            hash_result = self._calculate_hash(data, nonce)
            hashes += 1

            # Update hashrate every second
            if time.time() - start_time >= 1:
                self.hashrate = hashes / (time.time() - start_time)
                hashes = 0
                start_time = time.time()

            if int(hash_result, 16) < int(target, 16):
                asyncio.run(self._submit_share(
                    work_data["work_id"],
                    nonce,
                    hash_result
                ))

    async def _display_stats(self):
        """Display mining statistics"""
        while self.running:
            runtime = time.time() - self.start_time
            self.logger.info(
                f"\nMinerT1 Stats:"
                f"\n----------------"
                f"\nWorker: {self.worker_name}"
                f"\nThreads: {self.threads}"
                f"\nRuntime: {int(runtime)}s"
                f"\nHashrate: {self.hashrate:.2f} H/s"
                f"\nShares: {self.shares_accepted}/{self.shares_submitted}"
                f"\nPool: {self.pool_url}"
                f"\n----------------"
            )
            await asyncio.sleep(10)

    async def start(self):
        """Start mining"""
        self.logger.info(f"Starting MinerT1 with {self.threads} threads")
        self.logger.info(f"Connecting to pool: {self.pool_url}")
        self.logger.info(f"Worker name: {self.worker_name}")
        
        await self._init_session()
        self.running = True
        
        # Start stats display task
        asyncio.create_task(self._display_stats())
        
        while self.running:
            try:
                work = await self._get_work()
                if not work:
                    await asyncio.sleep(1)
                    continue

                # Start mining threads
                with ThreadPoolExecutor(max_workers=self.threads) as executor:
                    futures = []
                    for thread_id in range(self.threads):
                        futures.append(
                            executor.submit(
                                self._mining_thread,
                                thread_id,
                                work
                            )
                        )

                await asyncio.sleep(1)  # Check for new work every second

            except Exception as e:
                self.logger.error(f"Mining error: {e}")
                await asyncio.sleep(1)

    def stop(self):
        """Stop mining"""
        self.running = False
        if self.session:
            asyncio.run(self.session.close())
        self.logger.info("Mining stopped")

def main():
    parser = argparse.ArgumentParser(description="MinerT1 - TalantChain CPU Miner")
    parser.add_argument("--pool", required=True, help="Pool URL")
    parser.add_argument("--wallet", required=True, help="Wallet address")
    parser.add_argument("--worker", help="Worker name (optional)")
    parser.add_argument("--threads", type=int, help="Number of mining threads")
    parser.add_argument("--tor", action="store_true", help="Use Tor network")
    
    args = parser.parse_args()

    miner = MinerT1(
        pool_url=args.pool,
        wallet_address=args.wallet,
        worker_name=args.worker,
        threads=args.threads,
        use_tor=args.tor
    )

    try:
        asyncio.run(miner.start())
    except KeyboardInterrupt:
        miner.stop()
        print("\nMining stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        miner.stop()

if __name__ == "__main__":
    main()
