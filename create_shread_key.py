import asyncio
import logging
from AQE.kex import QuantumSafeKEX
from AQE.configuration import ConfigurationManager

# ロギングの設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def initialize_shared_key(config_file="config.ini",owner_shread_key_bin="shared_key_owner.bin"):
    """
    量子耐性鍵交換を用いて共通鍵を生成し、
    その鍵を "shared_key.bin" ファイルに書き込みます。

    Args:
        config_file (str): 設定ファイルのパス。サンプルでは "config.ini" を使用。

    Returns:
        bytes: 生成された共通鍵（shared_secret）。
    """
    logger.info("Initializing secure key exchange...")
    # 設定マネージャーを生成
    logger.debug(f"Loading configuration from {config_file}")
    config = ConfigurationManager(config_file)
    logger.debug(f"Loading owner shread key...")
    base_shread_key = ""
    try:
        with open(owner_shread_key_bin,"rb") as osk:
            base_shread_key = osk.read()
    except FileNotFoundError as identifier:
        logger.error(f"owner shread key not found: {identifier}")

    logger.debug("Creating QuantumSafeKEX instances")
    kex = QuantumSafeKEX(config_manager=config)
    shared_secret = kex.awa
    shared_key_file = "shared_key.bin"
    logger.info("key exchange between Owner and Me")
    shared_secret, ciphertext = await kex.exchange(base_shread_key)
    with open(shared_key_file, "wb") as f:
        f.write(shared_secret)
    logger.info(f"Shared key written to {shared_key_file}")

    return shared_secret

if __name__ == "__main__":
    logger.info("Starting key exchange and writing shared key to file")
    shared_key = asyncio.run(initialize_shared_key())
