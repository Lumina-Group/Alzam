import asyncio
import logging
from AQE.kex import QuantumSafeKEX
from AQE.configuration import ConfigurationManager

# ロギングの設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def initialize_shared_key(config_file="config.ini"):
    # 設定マネージャーを生成
    logger.debug(f"Loading configuration from {config_file}")
    config = ConfigurationManager(config_file)
    logger.debug("Creating QuantumSafeKEX instances")
    kex = QuantumSafeKEX(config_manager=config)
    shared_secret = kex.awa
    shared_key_file = "shared_key_owner.bin"
    with open(shared_key_file, "wb") as f:
        f.write(shared_secret)
    logger.info(f"Shared key written to {shared_key_file}")

    return shared_secret

if __name__ == "__main__":
    shared_key = asyncio.run(initialize_shared_key())
