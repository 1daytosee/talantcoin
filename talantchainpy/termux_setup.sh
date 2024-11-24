#!/data/data/com.termux/files/usr/bin/bash

# Update package lists
pkg update -y && pkg upgrade -y

# Install required packages
pkg install -y python clang make openssl libffi libsodium git

# Install Python dependencies
pip install --upgrade pip
pip install wheel
pip install setuptools

# Clone TalantChain repository
git clone https://github.com/yourusername/talantchainpy.git
cd talantchainpy

# Install Python requirements
pip install -r requirements.txt

echo "TalantChain setup completed!"
echo "You can now start using TalantChain."
