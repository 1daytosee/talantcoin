"""Node Manager for TalantChain"""

import asyncio
from typing import Optional
from .p2p.node import Node
import json
import os
from pathlib import Path

class NodeManager:
    _instance = None
    _node = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NodeManager, cls).__new__(cls)
        return cls._instance
        
    @classmethod
    def get_node(cls) -> Optional[Node]:
        """Get the current node instance"""
        return cls._node
        
    def create_node(self, host: str, port: int) -> Node:
        """Create and start a new node"""
        if self._node:
            self._node.stop()
            
        # Create event loop if it doesn't exist
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        # Create and start node
        self._node = Node(host, port)
        loop.run_until_complete(self._node.start())
        
        print(f"Node started on {host}:{port}")
        return self._node
        
    @classmethod
    async def start_node(cls, host: str, port: int) -> Node:
        """Start a new node asynchronously"""
        if cls._node:
            await cls._node.stop()
            
        cls._node = Node(host, port)
        await cls._node.start()
        return cls._node
        
    def stop_node(self):
        """Stop the current node"""
        if self._node:
            asyncio.run(self._node.stop())
            self._node = None
            
    def save_state(self, filepath: str):
        """Save node state to file"""
        if not self._node:
            return
            
        state = {
            'host': self._node.host,
            'port': self._node.port,
            'peers': [{'host': p.host, 'port': p.port} for p in self._node.peers],
            'blockchain': self._node.blockchain.to_dict()
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(state, f)
            
    def load_state(self, filepath: str):
        """Load node state from file"""
        if not os.path.exists(filepath):
            return
            
        with open(filepath, 'r') as f:
            state = json.load(f)
            
        # Create node with saved state
        self.create_node(state['host'], state['port'])
        
        # Restore blockchain and peers
        self._node.blockchain.from_dict(state['blockchain'])
        for peer in state['peers']:
            asyncio.run(self._node.connect_to_peer(peer['host'], peer['port']))
