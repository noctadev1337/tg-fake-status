import asyncio
from datetime import datetime, timezone
from telethon import TelegramClient
from telethon.tl.functions.account import UpdateStatusRequest

BLOCK_SECONDS = 240   # 4 минуты онлайн
PAUSE_SECONDS = 20    # пауза между блоками

class ActivityBot:
    def __init__(self, config):
        self.config = config
        self.client = TelegramClient(
            config.session_path,
            config.api_id,
            config.api_hash
        )
        self._session_task = None

    async def connect(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            raise RuntimeError("Сессия не авторизована. Запустите auth_qr.py")

    def make_session_handler(self, end_h, end_m):
        async def handler():
            ts = lambda: datetime.now().strftime("%H:%M:%S")
            print(f"  [{ts()}] сессия запущена (конец UTC {end_h:02d}:{end_m:02d})")

            while True:
                now = datetime.now(timezone.utc)
                end = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)

                # если конец уже прошёл сегодня — выходим
                remaining = (end - now).total_seconds()
                if remaining <= 30:
                    print(f"  [{ts()}] сессия завершена")
                    break

                block = min(BLOCK_SECONDS, remaining - 15)
                if block <= 0:
                    break

                await self.client(UpdateStatusRequest(offline=False))
                print(f"  [{ts()}] -> online  (блок {int(block)}с)")
                await asyncio.sleep(block)

                await self.client(UpdateStatusRequest(offline=True))
                print(f"  [{ts()}] -> offline (пауза {PAUSE_SECONDS}с)")

                now = datetime.now(timezone.utc)
                if (end - now).total_seconds() <= 30:
                    print(f"  [{ts()}] сессия завершена")
                    break

                await asyncio.sleep(PAUSE_SECONDS)

        return handler

    async def go_offline(self):
        if self._session_task and not self._session_task.done():
            self._session_task.cancel()
            await asyncio.gather(self._session_task, return_exceptions=True)
        await self.client(UpdateStatusRequest(offline=True))
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] -> offline (принудительно)")

    async def disconnect(self):
        await self.client.disconnect()
