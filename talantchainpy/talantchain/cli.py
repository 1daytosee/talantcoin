"""Command line interface for TalantChain"""

import os
import click
import getpass
from decimal import Decimal
from .node.node import Node
from .mining.miner import Miner
from .pool.miner import PoolMiner
from .pool.server import MiningPool
from .pool.web import PoolWebServer, PoolConfig
from .wallet.wallet import Wallet

@click.group()
def cli():
    """TalantChain CLI"""
    pass

@cli.command()
def start():
    """Start TalantChain node"""
    import asyncio
    node = Node()
    asyncio.run(node.start())

@cli.command()
@click.option('--address', prompt='Enter wallet address', help='Miner wallet address')
def startmining(address):
    """Start solo mining"""
    import asyncio
    miner = Miner(address=address)
    asyncio.run(miner.start_mining())

@cli.command()
@click.option('--pool', required=True, help='Pool URL')
@click.option('--address', required=True, help='Wallet address')
@click.option('--worker', help='Worker name')
@click.option('--threads', type=int, help='Number of mining threads')
@click.option('--tor', is_flag=True, help='Use Tor network')
def startpool(pool, address, worker, threads, tor):
    """Start pool mining"""
    import asyncio
    miner = PoolMiner(
        pool_url=pool,
        wallet_address=address,
        worker_name=worker,
        threads=threads,
        use_tor=tor
    )
    asyncio.run(miner.start())

@cli.command()
@click.option('--config', default='pool_config.json', help='Pool configuration file')
def startpoolserver(config):
    """Start mining pool server"""
    import asyncio
    pool_config = PoolConfig(config)
    pool = MiningPool(
        pool_address=pool_config.pool_address,
        fee=pool_config.fee,
        min_payout=pool_config.min_payout
    )
    web_server = PoolWebServer(
        pool=pool,
        host=pool_config.host,
        port=pool_config.port,
        ssl_cert=pool_config.ssl_cert,
        ssl_key=pool_config.ssl_key,
        tor_host=pool_config.tor_host,
        tor_port=pool_config.tor_port
    )
    asyncio.run(web_server.start())

@cli.command()
def createwallet():
    """Create new wallet"""
    name = input("Enter wallet name: ")
    password = getpass.getpass()
    confirm = getpass.getpass("Confirm password: ")
    
    if password != confirm:
        click.echo("Passwords do not match")
        return
        
    try:
        wallet = Wallet(name)
        address = wallet.create(password)
        click.echo(f"Wallet created successfully!")
        click.echo(f"Address: {address}")
    except Exception as e:
        click.echo(f"Error creating wallet: {str(e)}")

@cli.command()
def balance():
    """Check wallet balance"""
    name = input("Enter wallet name: ")
    password = getpass.getpass()
    
    try:
        wallet = Wallet(name)
        wallet.load(password)
        balance = wallet.get_balance()
        click.echo(f"Balance: {balance} TLNT")
    except Exception as e:
        click.echo(f"Error checking balance: {str(e)}")

@cli.command()
def send():
    """Send transaction"""
    name = input("Enter wallet name: ")
    password = getpass.getpass()
    recipient = input("Enter recipient address: ")
    amount = Decimal(input("Enter amount: "))
    
    try:
        wallet = Wallet(name)
        wallet.load(password)
        tx_hash = wallet.send(recipient, amount)
        click.echo(f"Transaction sent successfully!")
        click.echo(f"Transaction hash: {tx_hash}")
    except Exception as e:
        click.echo(f"Error sending transaction: {str(e)}")

@cli.command()
def listwallets():
    """List all wallets"""
    wallets = Wallet.list_wallets()
    if not wallets:
        click.echo("No wallets found")
        return
        
    click.echo("Available wallets:")
    for wallet in wallets:
        click.echo(f"- {wallet}")

if __name__ == '__main__':
    cli()
