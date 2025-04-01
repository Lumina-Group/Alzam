import logging
import asyncio
import base64 # 必要に応じて使用
from AQE.transport import SecureTransport
from AQE.configuration import ConfigurationManager # 元のコードのクラスを想定

logger = logging.getLogger(__name__)

class ConfigurationManagerWithKey(ConfigurationManager):
    def get_shared_key(self) -> bytes | None:
        """設定ファイルから共有鍵を取得する"""
        try:
            # [Security] セクションから shared_key を取得
            key_str = self.config.get('Security', 'shared_key', fallback=None)
            if key_str:
                # 文字列をバイト列に変換 (UTF-8を仮定)
                # ライブラリが特定のエンコーディングや形式を要求する場合はそれに合わせる
                return key_str.encode('utf-8')

            # Base64エンコードされた鍵を試す場合
            # key_b64 = self.config.get('Security', 'shared_key_base64', fallback=None)
            # if key_b64:
            #     return base64.b64decode(key_b64)

            logger.error("Shared key ('shared_key' or 'shared_key_base64') not found in [Security] section of config.")
            return None
        except Exception as e:
            logger.error(f"Error reading shared key from config: {e}")
            return None

async def process_file(mode: str, input_path: str, output_path: str, config_file: str):
    """ファイルを暗号化または復号化する"""
    action = "Encrypting" if mode == "encrypt" else "Decrypting"
    logger.info(f"{action} file: {input_path} -> {output_path}")

    try:
        # 拡張された ConfigurationManager を使用
        config_manager = ConfigurationManagerWithKey(config_file)
        shared_key = config_manager.get_shared_key()

        if not shared_key:
            logger.error("Failed to obtain shared key from configuration.")
            return False

        # SecureTransport を共通鍵で初期化
        transport = SecureTransport(initial_key=shared_key, config_manager=config_manager)

        # ファイルをチャンクで処理
        chunk_size = 4096 # 4KBずつ処理 (メモリ使用量を抑える)
        # 暗号化/復号化処理によっては、適切なチャンクサイズや
        # 暗号化後のデータ形式（ヘッダー、パディング等）の考慮が必要な場合があります。
        # AQE.SecureTransport の仕様を確認してください。

        async with asyncio.TaskGroup() as tg: # Python 3.11+
             # Python 3.10以前の場合は await asyncio.gather(...) などを使用
             infile = await tg.create_task(aiofiles.open(input_path, mode='rb'))
             outfile = await tg.create_task(aiofiles.open(output_path, mode='wb'))

             while True:
                 chunk = await infile.read(chunk_size)
                 if not chunk:
                     break

                 if mode == "encrypt":
                     processed_chunk = await transport.encrypt(chunk)
                 else: # decrypt
                     processed_chunk = await transport.decrypt(chunk)

                 await outfile.write(processed_chunk)

        # Note: 上記は単純なチャンク処理です。
        # SecureTransport の encrypt/decrypt がステートフルな場合
        # (例: 前のデータに依存するモード)、単純なチャンク処理では
        # 問題が発生する可能性があります。ライブラリのドキュメントを確認してください。
        # ストリーミングAPIがあれば、そちらを使うのが望ましいです。

        logger.info(f"File {action.lower()}ion successful.")
        return True

    except FileNotFoundError:
        logger.error(f"Input file not found: {input_path}")
        return False
    except Exception as e:
        # 復号エラー（鍵間違い、データ破損など）もここでキャッチされる
        logger.error(f"{action} failed: {e}", exc_info=True)
        # エラーが発生した場合、不完全な出力ファイルが残る可能性があるため削除する
        try:
            import os
            if os.path.exists(output_path):
                os.remove(output_path)
                logger.info(f"Removed incomplete output file: {output_path}")
        except OSError as rm_err:
            logger.error(f"Failed to remove incomplete output file {output_path}: {rm_err}")
        return False

# 非同期ファイルI/Oのために aiofiles ライブラリが必要
# pip install aiofiles
try:
    import aiofiles
except ImportError:
    logger.error("Please install 'aiofiles' library: pip install aiofiles")
    # aiofiles がない場合のフォールバック (同期処理になる)
    import os
    async def open_async(file, mode):
        return open(file, mode)
    class SyncFileWrapper:
        def __init__(self, f):
            self._f = f
        async def read(self, size=-1):
            return self._f.read(size)
        async def write(self, data):
            return self._f.write(data)
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            self._f.close()

    # aiofiles.open の代わりに使用するラッパー
    class AiofilesFallback:
        async def open(self, file, mode):
             f = open(file, mode)
             return SyncFileWrapper(f)
    aiofiles = AiofilesFallback()

async def encrypt_file(input_path: str, output_path: str, config_file: str = "config.ini"):
    """ファイルを暗号化する"""
    return await process_file("encrypt", input_path, output_path, config_file)

async def decrypt_file(input_path: str, output_path: str, config_file: str = "config.ini"):
    """ファイルを復号化する"""
    return await process_file("decrypt", input_path, output_path, config_file)