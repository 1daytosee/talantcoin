"""Database implementation for TalantChain"""

import sqlite3
import json
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional

class Database:
    def __init__(self, db_path: str = "blockchain.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Create blocks table
        c.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            height INTEGER PRIMARY KEY,
            hash TEXT UNIQUE,
            previous_hash TEXT,
            timestamp INTEGER,
            difficulty INTEGER,
            nonce INTEGER,
            miner_address TEXT,
            transactions TEXT,
            reward DECIMAL(16,8)
        )
        ''')

        # Create balances table
        c.execute('''
        CREATE TABLE IF NOT EXISTS balances (
            address TEXT PRIMARY KEY,
            amount DECIMAL(16,8) DEFAULT 0
        )
        ''')

        # Create transactions table
        c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            hash TEXT PRIMARY KEY,
            sender TEXT,
            recipient TEXT,
            amount DECIMAL(16,8),
            timestamp INTEGER,
            block_height INTEGER,
            FOREIGN KEY(block_height) REFERENCES blocks(height)
        )
        ''')

        conn.commit()
        conn.close()

    def get_height(self) -> int:
        """Get current blockchain height"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT MAX(height) FROM blocks')
        height = c.fetchone()[0] or 0
        conn.close()
        return height

    def get_latest_block_hash(self) -> str:
        """Get hash of latest block"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT hash FROM blocks ORDER BY height DESC LIMIT 1')
        result = c.fetchone()
        conn.close()
        return result[0] if result else "0" * 64

    def get_difficulty(self) -> int:
        """Get current mining difficulty"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT difficulty FROM blocks ORDER BY height DESC LIMIT 1')
        result = c.fetchone()
        conn.close()
        return result[0] if result else 1

    def increase_difficulty(self):
        """Increase mining difficulty"""
        current = self.get_difficulty()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('UPDATE blocks SET difficulty = ? WHERE height = (SELECT MAX(height) FROM blocks)',
                 (current + 1,))
        conn.commit()
        conn.close()

    def decrease_difficulty(self):
        """Decrease mining difficulty"""
        current = self.get_difficulty()
        if current > 1:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('UPDATE blocks SET difficulty = ? WHERE height = (SELECT MAX(height) FROM blocks)',
                     (current - 1,))
            conn.commit()
            conn.close()

    def get_balance(self, address: str) -> Decimal:
        """Get balance for address"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT amount FROM balances WHERE address = ?', (address,))
        result = c.fetchone()
        conn.close()
        return Decimal(str(result[0])) if result else Decimal('0')

    def add_balance(self, address: str, amount: Decimal):
        """Add amount to address balance"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        current = self.get_balance(address)
        new_amount = current + amount
        c.execute('''
        INSERT INTO balances (address, amount) VALUES (?, ?)
        ON CONFLICT(address) DO UPDATE SET amount = ?
        ''', (address, new_amount, new_amount))
        conn.commit()
        conn.close()

    def subtract_balance(self, address: str, amount: Decimal):
        """Subtract amount from address balance"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        current = self.get_balance(address)
        new_amount = current - amount
        if new_amount < 0:
            raise ValueError("Insufficient balance")
        c.execute('''
        INSERT INTO balances (address, amount) VALUES (?, ?)
        ON CONFLICT(address) DO UPDATE SET amount = ?
        ''', (address, new_amount, new_amount))
        conn.commit()
        conn.close()

    def add_block(self, block_data: dict):
        """Add new block to blockchain"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Insert block
        c.execute('''
        INSERT INTO blocks (
            height, hash, previous_hash, timestamp, difficulty,
            nonce, miner_address, transactions, reward
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            block_data['height'],
            block_data['hash'],
            block_data['previous_hash'],
            block_data['timestamp'],
            block_data['difficulty'],
            block_data['nonce'],
            block_data['miner_address'],
            json.dumps(block_data['transactions']),
            block_data['reward']
        ))
        
        # Insert transactions
        for tx in block_data['transactions']:
            c.execute('''
            INSERT INTO transactions (
                hash, sender, recipient, amount, timestamp, block_height
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                tx['hash'],
                tx['sender'],
                tx['recipient'],
                tx['amount'],
                tx['timestamp'],
                block_data['height']
            ))
        
        conn.commit()
        conn.close()

    def get_last_n_blocks(self, n: int) -> List[Dict]:
        """Get last n blocks"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
        SELECT height, hash, previous_hash, timestamp, difficulty,
               nonce, miner_address, transactions, reward
        FROM blocks ORDER BY height DESC LIMIT ?
        ''', (n,))
        
        blocks = []
        for row in c.fetchall():
            blocks.append({
                'height': row[0],
                'hash': row[1],
                'previous_hash': row[2],
                'timestamp': row[3],
                'difficulty': row[4],
                'nonce': row[5],
                'miner_address': row[6],
                'transactions': json.loads(row[7]),
                'reward': str(row[8])
            })
        
        conn.close()
        return blocks
