"""TalantChain Mining Client (similar to XMRig)"""

import argparse
import requests
import time
import json
from typing import Optional
import threading
from ..core.block import Block
from ..crypto.hash import Hash
from .miner import Miner

class MiningClient:
    def __init__(self):
        self.pool_url = None
        self.wallet_address = None
        self.threads = 1
        self.algorithm = "talant"  # Default algorithm
        self.miner = Miner()
        self._stop_flag = threading.Event()
        
    def start(self, pool_url: str, wallet_address: str, threads: int = 1):
        """Start mining with specified parameters"""
        self.pool_url = pool_url
        self.wallet_address = wallet_address
        self.threads = threads
        
        print(f"Starting TalantChain Miner")
        print(f"Pool: {pool_url}")
        print(f"Wallet: {wallet_address}")
        print(f"Threads: {threads}")
        
        # Start mining threads
        self._stop_flag.clear()
        for _ in range(threads):
            thread = threading.Thread(target=self._mining_thread)
            thread.daemon = True
            thread.start()
            
        # Start status thread
        status_thread = threading.Thread(target=self._status_thread)
        status_thread.daemon = True
        status_thread.start()
        
        try:
            while not self._stop_flag.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
            
    def stop(self):
        """Stop mining"""
        self._stop_flag.set()
        self.miner.stop_mining()
        print("\nMining stopped")
        
    def _mining_thread(self):
        """Mining worker thread"""
        while not self._stop_flag.is_set():
            try:
                # Get mining job from pool
                job = self._get_mining_job()
                if not job:
                    time.sleep(1)
                    continue
                    
                # Mine the block
                block = self._mine_block(job)
                if block:
                    # Submit solution
                    if self._submit_block(block):
                        print(f"\nBlock found and accepted! Hash: {block.hash.hex()}")
                    else:
                        print("\nBlock rejected by pool")
                        
            except Exception as e:
                print(f"\nMining error: {e}")
                time.sleep(1)
                
    def _status_thread(self):
        """Thread to display mining status"""
        while not self._stop_flag.is_set():
            try:
                hashrate = self.miner.get_hashrate()
                accepted = self.miner.blocks_found
                rejected = self.miner.blocks_rejected
                
                print(f"\rMining: {hashrate:,.0f} H/s | Accepted: {accepted} | Rejected: {rejected}", end="")
                time.sleep(1)
                
            except Exception as e:
                print(f"\nStatus error: {e}")
                time.sleep(1)
                
    def _get_mining_job(self) -> Optional[dict]:
        """Get mining job from pool"""
        try:
            response = requests.get(f"{self.pool_url}/mining/job", 
                                  params={"wallet": self.wallet_address})
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"\nError getting job: {e}")
        return None
        
    def _submit_block(self, block: Block) -> bool:
        """Submit solved block to pool"""
        try:
            response = requests.post(
                f"{self.pool_url}/mining/submit",
                json={
                    "wallet": self.wallet_address,
                    "block": block.to_dict()
                }
            )
            return response.status_code == 200
        except Exception as e:
            print(f"\nError submitting block: {e}")
            return False
            
def main():
    parser = argparse.ArgumentParser(description="TalantChain Mining Client")
    parser.add_argument("-o", "--pool", required=True, help="Pool URL (e.g., http://pool.talantchain.com:8334)")
    parser.add_argument("-u", "--wallet", required=True, help="Wallet address")
    parser.add_argument("-t", "--threads", type=int, default=1, help="Number of mining threads")
    parser.add_argument("-a", "--algo", default="talant", help="Mining algorithm")
    
    args = parser.parse_args()
    
    client = MiningClient()
    client.start(args.pool, args.wallet, args.threads)
    
if __name__ == "__main__":
    main()
