import aiohttp
import asyncio
import random
import time
import logging
from aiohttp_socks import ProxyConnector

logger = logging.getLogger(__name__)

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://www.proxyscan.io/download?type=http",
    "https://raw.githubusercontent.com/opsxcq/proxy-list/master/list.txt",
    "https://proxylist.geonode.com/api/proxy-list?protocols=http&limit=500",
    "https://api.openproxylist.xyz/http.txt",
    "https://multiproxy.org/txt_all/proxy.txt",
    "https://raw.githubusercontent.com/almroot/proxylist/master/list.txt",
    "https://www.freeproxychecker.com/result/http_proxies.txt",
    "https://proxy-spider.com/api/proxies.example.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",
    "https://raw.githubusercontent.com/UserR3X/proxy-list/main/http.txt"
]

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.last_update = 0
        self.update_interval = 1800  # 30 minutes
        self.valid_proxies = []
        self.validation_threshold = 10
        self.test_url = "https://api.ipify.org"

    async def fetch_proxies(self):
        """Fetch proxies from multiple sources"""
        all_proxies = []
        async with aiohttp.ClientSession() as session:
            tasks = []
            for source in PROXY_SOURCES:
                tasks.append(self._fetch_source(session, source))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    all_proxies.extend(result)
        
        # Deduplicate and format
        self.proxies = list(set([self._format_proxy(p) for p in all_proxies]))
        logger.info(f"Fetched {len(self.proxies)} proxies")
        self.last_update = time.time()
        await self.validate_proxies()
    
    async def _fetch_source(self, session, url):
        """Fetch proxies from a single source"""
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    text = await response.text()
                    return [line.strip() for line in text.splitlines() if line.strip()]
        except Exception as e:
            logger.debug(f"Failed to fetch {url}: {e}")
        return []

    def _format_proxy(self, proxy):
        """Standardize proxy format"""
        if "://" not in proxy:
            return f"http://{proxy}"
        return proxy

    async def validate_proxies(self):
        """Validate proxy functionality"""
        if not self.proxies:
            return
            
        logger.info("Validating proxies...")
        working_proxies = []
        semaphore = asyncio.Semaphore(50)  # Limit concurrency
        
        async def validate(proxy):
            async with semaphore:
                try:
                    connector = ProxyConnector.from_url(proxy)
                    async with aiohttp.ClientSession(connector=connector) as session:
                        async with session.get(self.test_url, timeout=10) as response:
                            if response.status == 200:
                                return proxy
                except Exception:
                    return None
        
        tasks = [validate(proxy) for proxy in self.proxies]
        results = await asyncio.gather(*tasks)
        self.valid_proxies = [p for p in results if p]
        logger.info(f"Validated {len(self.valid_proxies)} working proxies")

    async def get_random_proxy(self):
        """Get a random valid proxy with rotation"""
        if (time.time() - self.last_update > self.update_interval or 
            len(self.valid_proxies) < self.validation_threshold):
            await self.fetch_proxies()
            
        if not self.valid_proxies:
            return None
            
        return random.choice(self.valid_proxies)

    async def get_connector(self):
        """Get proxy connector for aiohttp"""
        proxy = await self.get_random_proxy()
        if proxy:
            try:
                return ProxyConnector.from_url(proxy)
            except Exception as e:
                logger.error(f"Invalid proxy format {proxy}: {e}")
        return None
