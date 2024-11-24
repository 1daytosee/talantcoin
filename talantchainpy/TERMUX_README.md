# TalantChain Setup Guide for Termux

This guide will help you install and run TalantChain on your Android device using Termux.

## Prerequisites

1. Install Termux from F-Droid (recommended) or Google Play Store
2. Make sure you have enough storage space (at least 1GB free)

## Installation Steps

1. First, install Termux from F-Droid:
   - Visit: https://f-droid.org/en/packages/com.termux/
   - Download and install the latest version

2. Open Termux and run these commands:
```bash
# Give storage permission to Termux
termux-setup-storage

# Update Termux
pkg update && pkg upgrade -y

# Install git
pkg install git -y

# Clone TalantChain repository
git clone https://github.com/yourusername/talantchainpy.git
cd talantchainpy

# Make setup script executable
chmod +x termux_setup.sh

# Run setup script
./termux_setup.sh
```

## Usage Commands

1. Start TalantChain Node:
```bash
python -m talantchain.cli start
```

2. Create a New Wallet:
```bash
python -m talantchain.cli createwallet
```

3. Start Solo Mining:
```bash
python -m talantchain.cli startmining --address YOUR_WALLET_ADDRESS
```

4. Start Pool Mining:
```bash
python -m talantchain.cli startpool --pool POOL_URL --address YOUR_WALLET_ADDRESS
```

5. Start Pool Server:
```bash
python -m talantchain.cli startpoolserver --config pool_config.json
```

## Common Issues and Solutions

1. If you get permission errors:
```bash
termux-setup-storage
```

2. If Python packages fail to install:
```bash
pkg install python-dev clang make -y
pip install --upgrade pip wheel setuptools
```

3. If you get SSL errors:
```bash
pkg install openssl -y
```

## Resource Management

Since Android devices have limited resources:

1. For mining, use fewer threads:
```bash
python -m talantchain.cli startpool --pool POOL_URL --address YOUR_WALLET_ADDRESS --threads 2
```

2. Monitor CPU temperature:
```bash
termux-battery-status
```

3. Keep Termux running in background:
```bash
# Install Termux:API
pkg install termux-api

# Enable wake lock
termux-wake-lock
```

## Tips for Better Performance

1. Use a cooling pad or keep your device in a cool place while mining
2. Close unnecessary background apps
3. Run mining during charging
4. Monitor device temperature regularly
5. Start with fewer threads and increase gradually

## Support

If you encounter any issues, please:
1. Check the error messages
2. Refer to this guide
3. Check GitHub issues
4. Create a new issue if needed

Remember that mining cryptocurrency can be resource-intensive. Monitor your device's temperature and battery health regularly.
