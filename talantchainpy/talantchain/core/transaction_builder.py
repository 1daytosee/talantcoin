"""Transaction builder for TalantChain"""

from typing import List, Tuple, Optional
from ..crypto.ring_signature import RingSignature
from ..crypto.address import Address
from .transaction import Transaction, Input, Output
import struct
import time
from decimal import Decimal

class TransactionBuilder:
    def __init__(self):
        self.inputs: List[Input] = []
        self.outputs: List[Output] = []
        self.ring_size = 11  # Default ring size
        
    def add_input(self, amount: Decimal, key_image: bytes, 
                  ring_members: List[bytes], private_key: bytes) -> None:
        """Add input to transaction"""
        input_data = Input(
            amount=amount,
            key_image=key_image,
            ring_members=ring_members
        )
        self.inputs.append(input_data)
        
    def add_output(self, amount: Decimal, destination: str) -> None:
        """Add output to transaction"""
        # Get recipient's public keys
        spend_public, view_public = Address.get_public_keys(destination)
        
        output_data = Output(
            amount=amount,
            recipient_spend_public=spend_public,
            recipient_view_public=view_public
        )
        self.outputs.append(output_data)
        
    def build(self, sender_private_key: bytes) -> Transaction:
        """Build final transaction"""
        if not self.inputs or not self.outputs:
            raise ValueError("Transaction must have at least one input and output")
            
        # Calculate transaction fee
        input_sum = sum(input_data.amount for input_data in self.inputs)
        output_sum = sum(output_data.amount for output_data in self.outputs)
        fee = input_sum - output_sum
        
        if fee < 0:
            raise ValueError("Insufficient input amount")
            
        # Create transaction data
        tx_data = struct.pack(
            "!Q",  # Timestamp
            int(time.time())
        )
        
        # Add inputs
        tx_data += struct.pack("!I", len(self.inputs))
        for input_data in self.inputs:
            tx_data += struct.pack("!Q", int(input_data.amount * 1e8))  # Convert to atomic units
            tx_data += input_data.key_image
            tx_data += struct.pack("!I", len(input_data.ring_members))
            for member in input_data.ring_members:
                tx_data += member
                
        # Add outputs
        tx_data += struct.pack("!I", len(self.outputs))
        for output_data in self.outputs:
            tx_data += struct.pack("!Q", int(output_data.amount * 1e8))  # Convert to atomic units
            tx_data += output_data.recipient_spend_public
            tx_data += output_data.recipient_view_public
            
        # Sign transaction
        signatures = []
        for i, input_data in enumerate(self.inputs):
            signature = RingSignature.sign(
                tx_data,
                input_data.ring_members,
                sender_private_key,
                0  # Real input is always at index 0 in ring
            )
            signatures.append(signature)
            
        # Create final transaction
        return Transaction(
            timestamp=int(time.time()),
            inputs=self.inputs,
            outputs=self.outputs,
            signatures=signatures,
            fee=fee
        )
        
    @staticmethod
    def create_coinbase(reward: Decimal, miner_address: str) -> Transaction:
        """Create coinbase transaction for mining reward"""
        builder = TransactionBuilder()
        
        # Add mining reward output
        builder.add_output(reward, miner_address)
        
        # Create special coinbase input
        builder.add_input(
            amount=reward,
            key_image=bytes(32),  # Empty key image for coinbase
            ring_members=[bytes(32)],  # Empty ring members
            private_key=bytes(32)  # Empty private key
        )
        
        # Build transaction without signatures (coinbase doesn't need them)
        tx = builder.build(bytes(32))
        tx.is_coinbase = True
        
        return tx
