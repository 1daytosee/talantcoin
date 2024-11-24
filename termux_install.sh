#!/data/data/com.termux/files/usr/bin/bash

echo "🚀 Setting up MinerT1 for Termux..."

# Update package lists
echo "📦 Updating package lists..."
pkg update -y && pkg upgrade -y

# Install required packages
echo "📥 Installing required packages..."
pkg install -y python python-dev clang make openssl libffi libsodium git rust

# Upgrade pip and install build tools
echo "🔧 Upgrading pip and installing build tools..."
python -m pip install --upgrade pip
python -m pip install --upgrade wheel
python -m pip install --upgrade setuptools
python -m pip install --upgrade cython

# Install dependencies
echo "📚 Installing Python dependencies..."
python -m pip install aiohttp==3.7.4  # Using older version for better compatibility
python -m pip install cryptography==3.4.0
python -m pip install requests==2.26.0
python -m pip install psutil==5.8.0

# Install MinerT1
echo "🔨 Installing MinerT1..."
python -m pip install -e .

echo "✅ MinerT1 installation completed!"
echo "You can now start mining using:"
echo "minert1 --pool POOL_URL --wallet YOUR_WALLET_ADDRESS [options]"
