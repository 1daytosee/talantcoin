"""Wallet implementation for TalantChain"""

import os
import json
import base64
from typing import Dict, Optional
from decimal import Decimal
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from ..crypto.keys import PrivateKey, PublicKey, generate_key_pair
from ..core.transaction import Transaction

class Wallet:
    def __init__(self, name: str):
        self.name = name
        self.wallet_dir = os.path.expanduser("~/.talantchain/wallets")
        self.wallet_path = os.path.join(self.wallet_dir, f"{name}.wallet")
        self.private_key: Optional[PrivateKey] = None
        self.public_key: Optional[PublicKey] = None
        self.address: Optional[str] = None

    @property
    def exists(self) -> bool:
        """Check if wallet file exists"""
        return os.path.exists(self.wallet_path)

    def create(self, password: str) -> str:
        """Create new wallet"""
        if self.exists:
            raise ValueError(f"Wallet {self.name} already exists")

        # Generate new key pair
        self.private_key, self.public_key = generate_key_pair()
        self.address = self.public_key.to_address()

        # Create wallet directory if it doesn't exist
        os.makedirs(self.wallet_dir, exist_ok=True)

        # Encrypt and save wallet
        self._save_wallet(password)

        return self.address

    def load(self, password: str) -> None:
        """Load wallet from file"""
        if not self.exists:
            raise ValueError(f"Wallet {self.name} does not exist")

        # Read encrypted wallet file
        with open(self.wallet_path, 'r') as f:
            encrypted_data = f.read()

        # Decrypt wallet data
        fernet = self._get_fernet(password)
        data = json.loads(fernet.decrypt(encrypted_data.encode()).decode())

        # Load keys
        self.private_key = PrivateKey.from_bytes(base64.b64decode(data['private_key']))
        self.public_key = PublicKey.from_bytes(base64.b64decode(data['public_key']))
        self.address = data['address']

    def create_transaction(self, recipient: str, amount: Decimal) -> Transaction:
        """Create new transaction"""
        if not self.private_key or not self.address:
            raise ValueError("Wallet not loaded")

        # Create transaction
        tx = Transaction(
            sender=self.address,
            recipient=recipient,
            amount=amount
        )

        # Sign transaction
        tx.sign(self.private_key)

        return tx

    def _save_wallet(self, password: str) -> None:
        """Save wallet to encrypted file"""
        if not self.private_key or not self.public_key or not self.address:
            raise ValueError("No wallet data to save")

        # Prepare wallet data
        data = {
            'private_key': base64.b64encode(self.private_key.to_bytes()).decode(),
            'public_key': base64.b64encode(self.public_key.to_bytes()).decode(),
            'address': self.address
        }

        # Encrypt and save
        fernet = self._get_fernet(password)
        encrypted_data = fernet.encrypt(json.dumps(data).encode())

        with open(self.wallet_path, 'w') as f:
            f.write(encrypted_data.decode())

    def _get_fernet(self, password: str) -> Fernet:
        """Get Fernet instance for encryption/decryption"""
        # Generate key from password using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'talantchain',  # Fixed salt for simplicity
            iterations=100000,
        )
        key = base64.b64encode(kdf.derive(password.encode()))
        return Fernet(key)

    def get_balance(self, node_url: str = "http://localhost:8080") -> Decimal:
        """Get wallet balance from node"""
        import requests
        if not self.address:
            raise ValueError("Wallet not loaded")

        try:
            response = requests.get(f"{node_url}/balance/{self.address}")
            response.raise_for_status()
            data = response.json()
            return Decimal(data['balance'])
        except Exception as e:
            raise ValueError(f"Error checking balance: {str(e)}")

    def send(self, recipient: str, amount: Decimal, node_url: str = "http://localhost:8080") -> str:
        """Send transaction to node"""
        import requests
        if not self.private_key or not self.address:
            raise ValueError("Wallet not loaded")

        try:
            # Create and sign transaction
            tx = self.create_transaction(recipient, amount)

            # Send to node
            response = requests.post(
                f"{node_url}/transaction",
                json=tx.to_dict()
            )
            response.raise_for_status()

            return tx.hash
        except Exception as e:
            raise ValueError(f"Error sending transaction: {str(e)}")

    @staticmethod
    def list_wallets() -> list:
        """List all available wallets"""
        wallet_dir = os.path.expanduser("~/.talantchain/wallets")
        if not os.path.exists(wallet_dir):
            return []

        wallets = []
        for file in os.listdir(wallet_dir):
            if file.endswith(".wallet"):
                wallets.append(file[:-7])  # Remove .wallet extension
        return wallets
