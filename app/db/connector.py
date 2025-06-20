import mysql.connector
from mysql.connector import pooling
from app.core.config import settings

# 建立一個連線池
pool = pooling.MySQLConnectionPool(
    # pool_name="fastapi_pool",
    pool_size=10,
    host=settings.db_host,
    # port=settings.db_port,
    user=settings.db_user,
    password=settings.db_password,
    database=settings.db_name,
    charset="utf8mb4",
    use_unicode=True,
    use_pure = True,
)
