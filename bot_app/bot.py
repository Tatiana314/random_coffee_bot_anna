import asyncio

import pytz
from aiogram import Bot, Dispatcher, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.config import settings
from database.engine import session_maker
from handlers.admin import admin_router
from handlers.base_commands import base_commands_router
from handlers.user_registration import user_reg_router
from middleware.dp import DataBaseSession

bot = Bot(settings.bot_token)
dp = Dispatcher()
dp.include_router(user_reg_router)
dp.include_router(base_commands_router)
dp.include_router(admin_router)
timezone = pytz.timezone('Europe/Moscow')
scheduler = AsyncIOScheduler(timezone=timezone)


# async def on_startup(bot):
#     run_param = False
#     if run_param:
#         await drop_db()
#     await create_db()


async def on_shutdown(bot):
    print('бот лег')


async def main():
    # dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


asyncio.run(main())