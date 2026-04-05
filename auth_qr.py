import asyncio
import qrcode
import sys
import os
sys.path.insert(0, '/root/tg-activity')

from core.config_manager import ConfigManager
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

async def main():
    config = ConfigManager()
    client = TelegramClient(config.session_path, config.api_id, config.api_hash)
    await client.connect()

    qr = await client.qr_login()
    print("\n  Сканируй QR: Настройки -> Устройства -> Подключить устройство\n")
    qr_img = qrcode.QRCode()
    qr_img.add_data(qr.url)
    qr_img.print_ascii(invert=True)

    try:
        await qr.wait(timeout=120)
        me = await client.get_me()
        print(f"\n  авторизован как @{me.username}")
    except SessionPasswordNeededError:
        pwd = input("  пароль 2FA: ")
        await client.sign_in(password=pwd)
        me = await client.get_me()
        print(f"  авторизован как @{me.username}")

    await client.disconnect()

asyncio.run(main())
