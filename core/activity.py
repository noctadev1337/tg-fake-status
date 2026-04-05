import asyncio
from datetime import datetime, timezone
from telethon import TelegramClient
from telethon.tl.functions.account import UpdateStatusRequest

BLOCK_SECONDS = 240
PAUSE_SECONDS = 5
PING_INTERVAL = 30

class ActivityBot:
    def __init__(self, config):
        self.config = config
        self.client = TelegramClient(
            config.session_path,
            config.api_id,
            config.api_hash
        )

    async def connect(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            raise RuntimeError("Сессия не авторизована. Запустите auth_qr.py")

    async def _online_block(self, seconds):
        """держим онлайн указанное кол-во секунд с пингом каждые 30с"""
        elapsed = 0
        await self.client(UpdateStatusRequest(offline=False))
        while elapsed < seconds:
            chunk = min(PING_INTERVAL, seconds - elapsed)
            await asyncio.sleep(chunk)
            elapsed += chunk
            if elapsed < seconds:
                await self.client(UpdateStatusRequest(offline=False))
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"  [{ts}] ping")

    def make_session_handler(self, end_h, end_m):
        async def handler():
            ts = lambda: datetime.now().strftime("%H:%M:%S")
            print(f"  [{ts()}] сессия запущена (конец UTC {end_h:02d}:{end_m:02d})")
            while True:
                now = datetime.now(timezone.utc)
                end = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
                remaining = (end - now).total_seconds()
                if remaining <= 30:
                    print(f"  [{ts()}] сессия завершена")
                    break
                block = min(BLOCK_SECONDS, remaining - 15)
                if block <= 0:
                    break
                print(f"  [{ts()}] -> online  (блок {int(block)}с)")
                await self._online_block(block)
                await self.client(UpdateStatusRequest(offline=True))
                print(f"  [{ts()}] -> offline (пауза {PAUSE_SECONDS}с)")
                now = datetime.now(timezone.utc)
                if (end - now).total_seconds() <= 30:
                    print(f"  [{ts()}] сессия завершена")
                    break
                await asyncio.sleep(PAUSE_SECONDS)
        return handler

    async def go_offline(self):
        await self.client(UpdateStatusRequest(offline=True))
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] -> offline (принудительно)")

    async def disconnect(self):
        await self.client.disconnect()
