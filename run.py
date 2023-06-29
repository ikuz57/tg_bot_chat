import logging
from app.tg_bot.bot import run_bot

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    run_bot()
