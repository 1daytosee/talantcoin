"""TalantChain Configuration"""

import os
from pathlib import Path

# Network configuration
NETWORK_ID = 1  # Mainnet
P2P_DEFAULT_PORT = 8333
RPC_DEFAULT_PORT = 8334

# Node configuration
DEFAULT_SEED_NODES = [
    ("127.0.0.1", 8333),  # Local seed node
]

# Data directory
def get_data_dir() -> Path:
    """Get data directory for blockchain data"""
    home = Path.home()
    if os.name == 'nt':  # Windows
        data_dir = home / "AppData" / "Roaming" / "TalantChain"
    else:  # Linux/Mac
        data_dir = home / ".talantchain"
    
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

# Node state file
NODE_STATE_FILE = get_data_dir() / "node_state.json"

# Mining configuration
MINING_REWARD_INITIAL = 50 * 100000000  # 50 coins in smallest unit
MINING_REWARD_HALVING_INTERVAL = 210000  # Blocks
TARGET_BLOCK_TIME = 60  # seconds

# Network protocol
PROTOCOL_VERSION = 1
USER_AGENT = f"TalantChain Core:{PROTOCOL_VERSION}"
