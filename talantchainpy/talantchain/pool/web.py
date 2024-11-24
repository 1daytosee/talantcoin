"""Pool web interface implementation"""

import os
import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2
import json
from typing import Optional
import logging
from .server import MiningPool
import ssl

class PoolWebServer:
    def __init__(self, pool: MiningPool, host: str = '0.0.0.0', port: int = 8081,
                 ssl_cert: Optional[str] = None, ssl_key: Optional[str] = None,
                 tor_host: Optional[str] = None, tor_port: Optional[int] = None):
        self.pool = pool
        self.host = host
        self.port = port
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self.tor_host = tor_host
        self.tor_port = tor_port
        self.app = web.Application()
        self._setup_routes()
        self._setup_templates()

    def _setup_routes(self):
        """Setup web routes"""
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/stats', self.handle_stats)
        self.app.router.add_get('/worker/{address}', self.handle_worker_stats)
        self.app.router.add_post('/submit', self.handle_submit)
        # Add static files
        self.app.router.add_static('/static/', path=os.path.join(
            os.path.dirname(__file__), 'static'),
            name='static'
        )

    def _setup_templates(self):
        """Setup Jinja2 templates"""
        aiohttp_jinja2.setup(
            self.app,
            loader=jinja2.FileSystemLoader(
                os.path.join(os.path.dirname(__file__), 'templates')
            )
        )

    @aiohttp_jinja2.template('index.html')
    async def handle_index(self, request):
        """Handle index page"""
        return {
            'pool_address': self.pool.pool_address,
            'stats': self.pool.get_stats()
        }

    async def handle_stats(self, request):
        """Handle stats request"""
        return web.json_response(self.pool.get_stats())

    async def handle_worker_stats(self, request):
        """Handle worker stats request"""
        address = request.match_info['address']
        stats = self.pool.get_worker_stats(address)
        return web.json_response(stats)

    async def handle_submit(self, request):
        """Handle share submission"""
        try:
            data = await request.json()
            result = await self.pool.submit_share(
                data['address'],
                data['worker_name'],
                data['nonce'],
                data['hash']
            )
            return web.json_response({'status': 'ok' if result else 'invalid'})
        except Exception as e:
            return web.json_response({'status': 'error', 'message': str(e)})

    async def start(self):
        """Start web server"""
        # Setup SSL if configured
        ssl_context = None
        if self.ssl_cert and self.ssl_key:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(self.ssl_cert, self.ssl_key)

        # Start clearnet server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port, ssl_context=ssl_context)
        await site.start()
        logging.info(f"Pool web interface running on http{'s' if ssl_context else ''}://{self.host}:{self.port}")

        # Start Tor hidden service if configured
        if self.tor_host and self.tor_port:
            tor_site = web.TCPSite(runner, self.tor_host, self.tor_port)
            await tor_site.start()
            logging.info(f"Pool web interface running on Tor: {self.tor_host}:{self.tor_port}")

class PoolConfig:
    """Pool configuration"""
    def __init__(self, config_file: str = 'pool_config.json'):
        self.config_file = config_file
        self.load()

    def load(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            self.pool_address = config.get('pool_address')
            self.fee = float(config.get('fee', 0.01))
            self.min_payout = float(config.get('min_payout', 1.0))
            self.host = config.get('host', '0.0.0.0')
            self.port = int(config.get('port', 8081))
            self.ssl_cert = config.get('ssl_cert')
            self.ssl_key = config.get('ssl_key')
            self.tor_host = config.get('tor_host')
            self.tor_port = int(config.get('tor_port', 9050)) if config.get('tor_port') else None
        except FileNotFoundError:
            self.create_default()
            self.load()

    def create_default(self):
        """Create default configuration file"""
        config = {
            'pool_address': '',  # Must be set by pool operator
            'fee': 0.01,
            'min_payout': 1.0,
            'host': '0.0.0.0',
            'port': 8081,
            'ssl_cert': '',
            'ssl_key': '',
            'tor_host': '',
            'tor_port': 9050
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)

async def main():
    """Main entry point"""
    # Load configuration
    config = PoolConfig()
    
    # Create and start pool
    pool = MiningPool(
        pool_address=config.pool_address,
        fee=config.fee,
        min_payout=config.min_payout
    )
    await pool.start()

    # Create and start web server
    web_server = PoolWebServer(
        pool=pool,
        host=config.host,
        port=config.port,
        ssl_cert=config.ssl_cert,
        ssl_key=config.ssl_key,
        tor_host=config.tor_host,
        tor_port=config.tor_port
    )
    await web_server.start()

    # Keep running
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())
