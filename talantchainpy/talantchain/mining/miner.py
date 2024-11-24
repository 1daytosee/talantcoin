"""Mining implementation for TalantChain with RandomX-like CPU mining"""

import asyncio
import aiohttp
import time
import json
import hashlib
import random
from decimal import Decimal
from typing import Optional, Dict
import psutil
from ..crypto.hash import Hash

class RandomXLite:
    """Simplified RandomX-like CPU mining algorithm"""
    def __init__(self):
        self.program_size = 256  # Size of random program
        self.memory_size = 2048  # KB of memory to use
        self.iterations = 2048   # Number of iterations

    def _generate_program(self, seed: bytes) -> bytes:
        """Generate pseudo-random program based on seed"""
        random.seed(seed)
        program = bytearray()
        for _ in range(self.program_size):
            instruction = random.randint(0, 255)
            program.append(instruction)
        return bytes(program)

    def _execute_program(self, program: bytes, input_data: bytes) -> bytes:
        """Execute random program on input data"""
        state = bytearray(input_data)
        memory = bytearray(self.memory_size * 1024)  # Allocated memory

        # Initialize memory with input
        for i in range(min(len(input_data), len(memory))):
            memory[i] = input_data[i]

        # Execute program iterations
        for _ in range(self.iterations):
            for i in range(0, len(program), 4):
                if i + 4 > len(program):
                    break

                # Get instruction and operands
                instr = program[i]
                op1 = program[i + 1]
                op2 = program[i + 2]
                op3 = program[i + 3]

                # Memory address
                addr = ((op1 << 16) | (op2 << 8) | op3) % len(memory)

                # Perform operation based on instruction
                if instr < 64:  # XOR operation
                    state[addr % len(state)] ^= memory[addr]
                elif instr < 128:  # ADD operation
                    state[addr % len(state)] = (state[addr % len(state)] + memory[addr]) & 0xFF
                elif instr < 192:  # MUL operation
                    state[addr % len(state)] = (state[addr % len(state)] * memory[addr]) & 0xFF
                else:  # ROT operation
                    state[addr % len(state)] = (state[addr % len(state)] << 1) & 0xFF

        # Final hash
        return hashlib.sha3_256(state).digest()

    def hash(self, data: bytes, seed: bytes) -> bytes:
        """Compute RandomX-like hash"""
        program = self._generate_program(seed)
        return self._execute_program(program, data)

class Block:
    def __init__(self, height: int, previous_hash: str, timestamp: int, difficulty: int):
        self.height = height
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.difficulty = difficulty
        self.nonce = 0
        self.transactions = []
        self.miner_address = None
        self.reward = Decimal('50.0')
        self.version = 1
        self.target_time = 60  # Target 60 seconds per block

    @classmethod
    def from_dict(cls, template: dict) -> 'Block':
        block = cls(
            height=template['height'],
            previous_hash=template['previous_hash'],
            timestamp=template['timestamp'],
            difficulty=template['difficulty']
        )
        block.transactions = template.get('transactions', [])
        block.miner_address = template.get('miner_address')
        block.reward = Decimal(template.get('reward', '50.0'))
        block.version = template.get('version', 1)
        return block

    def hash(self, randomx: RandomXLite) -> bytes:
        """Calculate block hash using RandomX-like algorithm"""
        data = {
            'version': self.version,
            'height': self.height,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'difficulty': self.difficulty,
            'nonce': self.nonce,
            'transactions': self.transactions,
            'miner_address': self.miner_address,
            'reward': str(self.reward)
        }
        input_data = json.dumps(data, sort_keys=True).encode()
        seed = hashlib.sha3_256(self.previous_hash.encode()).digest()
        return randomx.hash(input_data, seed)

    def meets_difficulty(self, hash_bytes: bytes, difficulty: int) -> bool:
        """Check if block hash meets difficulty requirement"""
        target = 2 ** (256 - difficulty)
        return int.from_bytes(hash_bytes, byteorder='big') < target

    def to_dict(self) -> dict:
        return {
            'version': self.version,
            'height': self.height,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'difficulty': self.difficulty,
            'nonce': self.nonce,
            'transactions': self.transactions,
            'miner_address': self.miner_address,
            'reward': str(self.reward),
            'hash': self.hash(RandomXLite()).hex()
        }

class Miner:
    def __init__(self, address: str, node_url: str = "http://localhost:8080"):
        self.address = address
        self.node_url = node_url
        self.running = False
        self.current_block = None
        self.blocks_found = 0
        self.total_rewards = Decimal('0')
        self.start_time = 0
        self.randomx = RandomXLite()
        self.session = None
        self.cpu_count = psutil.cpu_count(logical=False)  # Physical CPU cores only
        self.last_block_time = time.time()
        self.current_height = 0

    async def start_mining(self):
        """Start mining process"""
        print(f"\n🚀 Starting TalantChain Miner")
        print(f"💻 CPU Cores: {self.cpu_count}")
        print(f"🌐 Node URL: {self.node_url}")
        print(f"👛 Miner Address: {self.address}")
        print(f"⏱️  Target Block Time: 60 seconds")
        print("\n")

        self.running = True
        self.start_time = time.time()
        self.session = aiohttp.ClientSession()

        try:
            while self.running:
                # Get new block template
                template = await self.get_block_template()
                if not template:
                    await asyncio.sleep(1)
                    continue

                # Create block
                block = Block.from_dict(template)
                block.miner_address = self.address

                # Mine block
                mined_block = await self.mine_block(block)
                if mined_block:
                    # Submit block
                    if await self.submit_block(mined_block):
                        self.blocks_found += 1
                        self.total_rewards += Decimal(mined_block['reward'])
                        self.last_block_time = time.time()
                        
                        # Print block found message
                        print(f"\n🎉 Block found! Height: {mined_block['height']}")
                        print(f"⛏️  Hash: {mined_block['hash']}")
                        print(f"💰 Reward: {mined_block['reward']} TLNT")
                        print(f"📦 Transactions: {len(mined_block['transactions'])}")
                        print(f"⏱️  Time taken: {time.time() - self.last_block_time:.2f} seconds\n")

        except Exception as e:
            print(f"Error in mining loop: {e}")
        finally:
            if self.session:
                await self.session.close()

    async def get_block_template(self) -> Optional[Dict]:
        """Get block template from node"""
        try:
            async with self.session.get(
                f"{self.node_url}/getblocktemplate",
                params={'address': self.address}
            ) as response:
                if response.status == 200:
                    template = await response.json()
                    self.current_height = template['height']
                    return template
        except Exception as e:
            print(f"Error getting block template: {e}")
        return None

    async def submit_block(self, block: Dict) -> bool:
        """Submit block to node"""
        try:
            async with self.session.post(
                f"{self.node_url}/submitblock",
                json=block
            ) as response:
                return response.status == 200
        except Exception as e:
            print(f"Error submitting block: {e}")
            return False

    async def mine_block(self, block: Block) -> Optional[Dict]:
        """Mine a single block"""
        start_time = time.time()
        hashes = 0
        last_status = time.time()

        # Calculate target based on current time
        current_time = time.time()
        time_since_last = current_time - self.last_block_time

        while self.running:
            # Try to find valid nonce
            block.nonce += 1
            block_hash = block.hash(self.randomx)
            
            # Check if hash meets difficulty
            if block.meets_difficulty(block_hash, block.difficulty):
                # Only allow block to be mined after target time
                if time_since_last >= block.target_time:
                    block_dict = block.to_dict()
                    return block_dict
                else:
                    # Continue mining but don't submit yet
                    continue

            hashes += 1

            # Update status every second
            if time.time() - last_status >= 1:
                elapsed = time.time() - start_time
                hashrate = hashes / elapsed if elapsed > 0 else 0
                time_to_target = max(0, block.target_time - time_since_last)

                print(f"\r⛏️  Mining Block {block.height} | "
                      f"Hashrate: {self.format_hashrate(hashrate)} | "
                      f"Time to target: {time_to_target:.0f}s | "
                      f"Blocks: {self.blocks_found} | "
                      f"Rewards: {self.total_rewards:.8f} TLNT", end='')

                last_status = time.time()

        return None

    def format_hashrate(self, hashes_per_sec: float) -> str:
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
    parser = argparse.ArgumentParser(description='TalantChain Miner')
    parser.add_argument('--address', required=True, help='Miner address')
    parser.add_argument('--node', default='http://localhost:8080', help='Node URL')
    args = parser.parse_args()

    miner = Miner(args.address, args.node)
    await miner.start_mining()

if __name__ == '__main__':
    asyncio.run(main())
