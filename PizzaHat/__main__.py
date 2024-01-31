import logging
import os

from dotenv import load_dotenv

from core.bot import PizzaHat

load_dotenv()

logger = logging.getLogger("bot")

if __name__ == "__main__":
    bot = PizzaHat()
    bot.run(os.getenv("TOKEN"), root_logger=True)  # type: ignore
