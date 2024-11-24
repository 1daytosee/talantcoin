# MinerT1 - TalantChain CPU Miner

A lightweight, CPU-optimized cryptocurrency miner for TalantChain, designed to work seamlessly on various platforms including Android (Termux).

## Features

- CPU-optimized mining algorithm
- Multi-threaded mining
- Real-time statistics
- Tor network support
- Android compatibility via Termux
- Low memory footprint
- Automatic thread detection
- Custom worker names

## Installation

### Linux
```bash
# Clone repository
git clone https://github.com/yourusername/minert1.git
cd minert1

# Install
python3 -m pip install -e .
```

### Windows
```powershell
# Clone repository
git clone https://github.com/yourusername/minert1.git
cd minert1

# Install
pip install -e .
```

### Android (Termux)
```bash
# Install Termux from F-Droid
# Then run:
pkg install git python

# Clone repository
git clone https://github.com/yourusername/minert1.git
cd minert1

# Run installation script
chmod +x termux_install.sh
./termux_install.sh
```

## Usage

Basic mining:
```bash
minert1 --pool http://pool.example.com:8081 --wallet YOUR_WALLET_ADDRESS
```

Advanced options:
```bash
minert1 --pool http://pool.example.com:8081 --wallet YOUR_WALLET_ADDRESS --worker worker1 --threads 4 --tor
```

Options:
- `--pool`: Pool URL (required)
- `--wallet`: Your wallet address (required)
- `--worker`: Custom worker name (optional)
- `--threads`: Number of mining threads (optional)
- `--tor`: Use Tor network (optional)

## Termux Tips

1. Keep screen on while mining:
```bash
termux-wake-lock
```

2. Monitor temperature:
```bash
termux-battery-status
```

3. Run in background:
```bash
nohup minert1 --pool URL --wallet ADDRESS &
```

4. View logs:
```bash
tail -f nohup.out
```

## Performance Tips

1. Start with fewer threads on mobile devices
2. Monitor device temperature
3. Use a cooling pad or keep device in cool place
4. Close unnecessary background apps
5. Consider using a stable internet connection

## Support

If you encounter any issues:
1. Check error messages
2. Verify internet connection
3. Check pool status
4. Create an issue on GitHub

## License

MIT License - see LICENSE file

## Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

---
Made with ❤️ by TalantChain Team
