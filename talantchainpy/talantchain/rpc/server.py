"""RPC Server for TalantChain"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
import threading
from ..core.block import Block
from ..core.transaction import Transaction
from ..node_manager import NodeManager

app = FastAPI(title="TalantChain RPC")

class BlockchainStats(BaseModel):
    height: int
    difficulty: int
    hashrate: float
    peers: int
    transactions_in_pool: int

class MiningStatus(BaseModel):
    is_mining: bool
    hashrate: float
    blocks_found: int
    current_difficulty: int

class RPCServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8334):
        self.host = host
        self.port = port
        self.node = None
        
    def start(self):
        """Start RPC server in a separate thread"""
        thread = threading.Thread(target=self._run_server)
        thread.daemon = True
        thread.start()
        print(f"RPC server started at http://{self.host}:{self.port}")
        
    def _run_server(self):
        """Run the FastAPI server"""
        uvicorn.run(app, host=self.host, port=self.port)

# RPC Endpoints
@app.get("/stats", response_model=BlockchainStats)
async def get_stats():
    """Get blockchain statistics"""
    node = NodeManager.get_node()
    if not node:
        raise HTTPException(status_code=500, detail="Node not running")
        
    return {
        "height": len(node.blockchain.chain),
        "difficulty": node.blockchain.get_difficulty(),
        "hashrate": node.miner.get_hashrate() if hasattr(node, 'miner') else 0,
        "peers": len(node.peers),
        "transactions_in_pool": len(node.current_transactions)
    }

@app.get("/mining/status", response_model=MiningStatus)
async def get_mining_status():
    """Get mining status"""
    node = NodeManager.get_node()
    if not node or not hasattr(node, 'miner'):
        raise HTTPException(status_code=500, detail="Mining not initialized")
        
    return {
        "is_mining": node.miner.is_mining(),
        "hashrate": node.miner.get_hashrate(),
        "blocks_found": node.miner.blocks_found,
        "current_difficulty": node.blockchain.get_difficulty()
    }

@app.post("/mining/start")
async def start_mining(wallet_address: str):
    """Start mining to specified wallet address"""
    node = NodeManager.get_node()
    if not node:
        raise HTTPException(status_code=500, detail="Node not running")
        
    try:
        node.miner.start_mining(wallet_address)
        return {"status": "Mining started", "wallet": wallet_address}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mining/stop")
async def stop_mining():
    """Stop mining"""
    node = NodeManager.get_node()
    if not node or not hasattr(node, 'miner'):
        raise HTTPException(status_code=500, detail="Mining not initialized")
        
    node.miner.stop_mining()
    return {"status": "Mining stopped"}
