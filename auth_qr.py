import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import qrcode
from core.config_manager import ConfigManager
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

def ask(prompt):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    return sys.stdin.buffer.readline().decode("utf-8", errors="replace").strip()

async def main():
    config = ConfigManager()
    client = TelegramClient(config.session_path, config.api_id, config.api_hash)
    await client.connect()

    try:
        qr = await client.qr_login()
        print("\n  Сканируй QR: Настройки -> Устройства -> Подключить устройство\n")
        qr_img = qrcode.QRCode()
        qr_img.add_data(qr.url)
        qr_img.print_ascii(invert=True)

        try:
            await qr.wait(timeout=120)
        except SessionPasswordNeededError:
            pwd = ask("\n  Пароль 2FA: ")
            await client.sign_in(password=pwd)

        me = await client.get_me()
        print(f"\n  авторизован как @{me.username}")

    except KeyboardInterrupt:
        print("\n  отменено")
    finally:
        await client.disconnect()

asyncio.run(main())
