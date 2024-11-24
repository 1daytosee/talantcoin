"""Pool miner implementation"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Optional
import platform
import psutil
from ..mining.miner import RandomXLite

class PoolMiner:
    def __init__(self, pool_url: str, wallet_address: str, worker_name: Optional[str] = None,
                 threads: Optional[int] = None, use_tor: bool = False):
        self.pool_url = pool_url.rstrip('/')
        self.wallet_address = wallet_address
        self.worker_name = worker_name or platform.node()
        self.threads = threads or psutil.cpu_count(logical=False)
        self.use_tor = use_tor
        self.randomx = RandomXLite()
        self.running = False
        self.current_job = None
        self.total_shares = 0
        self.accepted_shares = 0
        self.rejected_shares = 0
        self.start_time = 0
        self.session = None
        self.proxy = "socks5://127.0.0.1:9050" if use_tor else None

    async def start(self):
        """Start mining"""
        print(f"\n🚀 Starting TalantChain Pool Miner")
        print(f"🌐 Pool: {self.pool_url}")
        print(f"👛 Address: {self.wallet_address}")
        print(f"👷 Worker: {self.worker_name}")
        print(f"💻 Threads: {self.threads}")
        print(f"🧅 Tor: {'Enabled' if self.use_tor else 'Disabled'}")
        print("\n")

        self.running = True
        self.start_time = time.time()
        
        # Create client session with Tor proxy if enabled
        if self.use_tor:
            conn = aiohttp.TCPConnector(ssl=False)  # Allow connection to .onion addresses
            self.session = aiohttp.ClientSession(connector=conn)
        else:
            self.session = aiohttp.ClientSession()

        # Start mining tasks
        tasks = []
        for _ in range(self.threads):
            task = asyncio.create_task(self._mine())
            tasks.append(task)

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logging.error(f"Mining error: {e}")
        finally:
            self.running = False
            if self.session:
                await self.session.close()

    async def _get_job(self) -> Optional[dict]:
        """Get mining job from pool"""
        try:
            async with self.session.get(
                f"{self.pool_url}/job",
                params={'address': self.wallet_address, 'worker': self.worker_name},
                proxy=self.proxy
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logging.error(f"Error getting job: {e}")
        return None

    async def _submit_share(self, job_id: str, nonce: int, hash_result: str) -> bool:
        """Submit share to pool"""
        try:
            data = {
                'address': self.wallet_address,
                'worker_name': self.worker_name,
                'job_id': job_id,
                'nonce': nonce,
                'hash': hash_result
            }
            async with self.session.post(
                f"{self.pool_url}/submit",
                json=data,
                proxy=self.proxy
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('status') == 'ok'
        except Exception as e:
            logging.error(f"Error submitting share: {e}")
        return False

    async def _mine(self):
        """Mining loop"""
        start_time = time.time()
        hashes = 0
        last_update = time.time()

        while self.running:
            # Get new job if needed
            if not self.current_job:
                self.current_job = await self._get_job()
                if not self.current_job:
                    await asyncio.sleep(1)
                    continue

            # Mine
            nonce = int(time.time() * 1000000)  # Use timestamp as starting nonce
            block_data = {
                'version': self.current_job['version'],
                'height': self.current_job['height'],
                'previous_hash': self.current_job['previous_hash'],
                'timestamp': self.current_job['timestamp'],
                'transactions': self.current_job['transactions'],
                'nonce': nonce
            }
            
            input_data = json.dumps(block_data, sort_keys=True).encode()
            seed = bytes.fromhex(self.current_job['seed'])
            hash_result = self.randomx.hash(input_data, seed)
            
            # Check if share meets difficulty
            hash_int = int.from_bytes(hash_result, byteorder='big')
            target = 2 ** (256 - self.current_job['difficulty'])
            
            if hash_int < target:
                # Submit share
                if await self._submit_share(
                    self.current_job['job_id'],
                    nonce,
                    hash_result.hex()
                ):
                    self.accepted_shares += 1
                else:
                    self.rejected_shares += 1
                self.total_shares += 1

            hashes += 1

            # Update status every second
            if time.time() - last_update >= 1:
                elapsed = time.time() - start_time
                hashrate = hashes / elapsed if elapsed > 0 else 0
                
                print(f"\r⛏️  Mining | "
                      f"Height: {self.current_job['height']} | "
                      f"Hashrate: {self._format_hashrate(hashrate)} | "
                      f"Shares: {self.accepted_shares}/{self.total_shares} | "
                      f"Rejected: {self.rejected_shares}", end='')
                
                last_update = time.time()

    def _format_hashrate(self, hashes_per_sec: float) -> str:
        """Format hashrate with appropriate unit"""
        if hashes_per_sec >= 1e9:
            return f"{hashes_per_sec/1e9:.2f} GH/s"
        elif hashes_per_sec >= 1e6:
            return f"{hashes_per_sec/1e6:.2f} MH/s"
        elif hashes_per_sec >= 1e3:
            return f"{hashes_per_sec/1e3:.2f} KH/s"
        else:
            return f"{hashes_per_sec:.2f} H/s"

async def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description='TalantChain Pool Miner')
    parser.add_argument('--pool', required=True, help='Pool URL')
    parser.add_argument('--address', required=True, help='Wallet address')
    parser.add_argument('--worker', help='Worker name')
    parser.add_argument('--threads', type=int, help='Number of mining threads')
    parser.add_argument('--tor', action='store_true', help='Use Tor network')
    args = parser.parse_args()

    miner = PoolMiner(
        pool_url=args.pool,
        wallet_address=args.address,
        worker_name=args.worker,
        threads=args.threads,
        use_tor=args.tor
    )
    await miner.start()

if __name__ == '__main__':
    asyncio.run(main())
