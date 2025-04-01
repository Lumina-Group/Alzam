import argparse
import asyncio
import logging
import os
import sys
# encryption_utils から関数をインポート
from encryption_utils import encrypt_file, decrypt_file, ConfigurationManagerWithKey

# --- ロギング設定 ---
# config.ini からログレベルを読み込む試み
def setup_logging(config_file="config.ini"):
    log_level_str = "INFO" # デフォルト
    if os.path.exists(config_file):
        try:
            # ここでは簡易的に設定を読む (ConfigParserを使うのがより堅牢)
            with open(config_file, 'r') as f:
                for line in f:
                    if line.strip().lower().startswith("log_level"):
                        level = line.split('=')[1].strip().upper()
                        if level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                            log_level_str = level
                        break
        except Exception:
            pass # エラー時はデフォルトを使用
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

async def run():
    parser = argparse.ArgumentParser(description="Encrypt or decrypt files using a shared key with AQE.")
    parser.add_argument("mode", choices=['encrypt', 'decrypt'], help="Operation mode: encrypt or decrypt")
    parser.add_argument("-i", "--input", required=True, help="Input file path")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument("-c", "--config", default="config.ini", help="Configuration file path (default: config.ini)")

    # 引数を解析する前にロギングを設定
    temp_args, _ = parser.parse_known_args()
    config_path = temp_args.config if temp_args.config else "config.ini"
    setup_logging(config_path)


    args = parser.parse_args()


    logger.debug(f"Mode: {args.mode}")
    logger.debug(f"Input: {args.input}")
    logger.debug(f"Output: {args.output}")
    logger.debug(f"Config: {args.config}")


    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1) # エラーで終了

    if not os.path.exists(args.config):
         logger.warning(f"Configuration file not found: {args.config}. Using default AQE settings if possible.")
         # 必須設定が config にしかない場合、ここでエラー終了させるべきかもしれない
         # sys.exit(1)


    # 出力ファイルが入力ファイルと同じ場合はエラー
    if os.path.abspath(args.input) == os.path.abspath(args.output):
        logger.error("Input and output file paths cannot be the same.")
        sys.exit(1)


    success = False
    if args.mode == 'encrypt':
        success = await encrypt_file(args.input, args.output, args.config)
    elif args.mode == 'decrypt':
        success = await decrypt_file(args.input, args.output, args.config)


    if success:
        logger.info("Operation completed successfully.")
        sys.exit(0) # 成功で終了
    else:
        logger.error("Operation failed.")
        sys.exit(1) # エラーで終了

if __name__ == "__main__":
    # aiofiles が必要
    try:
        import aiofiles
    except ImportError:
        print("Error: 'aiofiles' library is required. Please install it using: pip install aiofiles", file=sys.stderr)
        sys.exit(1)

    # AQE ライブラリの存在確認 (簡易)
    try:
        from AQE.transport import SecureTransport
        from AQE.configuration import ConfigurationManager
    except ImportError:
        print("Error: AQE library components (SecureTransport, ConfigurationManager) not found.", file=sys.stderr)
        print("Please ensure the AQE library is correctly installed or available in the PYTHONPATH.", file=sys.stderr)
        sys.exit(1)

    asyncio.run(run())