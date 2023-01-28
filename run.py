from aiogram import executor
from bot.bot_controller import dp
from bot.middlewares import AlbumMiddleware


if __name__ == "__main__":
    dp.middleware.setup(AlbumMiddleware())
    executor.start_polling(dp, skip_updates=True, timeout=10000000)

