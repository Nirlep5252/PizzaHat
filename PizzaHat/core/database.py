import os
import ssl

import asyncpg  # type: ignore
from dotenv import load_dotenv

load_dotenv()


# Change this to `False` if you are using localhost for postgres
ENABLE_SSL = True


async def create_db_pool():
    ssl_object = ssl.create_default_context()
    ssl_object.check_hostname = False
    ssl_object.verify_mode = ssl.CERT_NONE

    if not ENABLE_SSL:
        return await asyncpg.create_pool(dsn=os.getenv("PG_URL"))
    return await asyncpg.create_pool(dsn=os.getenv("PG_URL"), enable_ssl=ssl_object)
