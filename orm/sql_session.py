
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import logging
logger = logging.getLogger(__name__)

from utils.config_util import get_db_config


db_config = get_db_config()

# 自动建库建表
connection = pymysql.connect(
    host=db_config["host"],
    user=db_config["user"],
    password=db_config["password"],
    port=int(db_config["port"]),
    charset='utf8mb4'
)
try:
    with connection.cursor() as cursor:

        db_name = db_config["db"]
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci")
        logger.info(f"创建库 {db_name} 成功")
        cursor.execute(f"USE `{db_name}`")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS short_term_memory (
            id INT AUTO_INCREMENT PRIMARY KEY,
            role CHAR(10) NOT NULL,
            send_time DATETIME NOT NULL,
            content MEDIUMTEXT NOT NULL,
            compact TINYINT(1) NOT NULL DEFAULT 0,
            status TINYINT(1) NOT NULL DEFAULT 1,
            tokens INT NOT NULL DEFAULT 0
            )
        """)
        logger.info(f"创建短期记忆表成功")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS mid_term_memory (
            id INT AUTO_INCREMENT PRIMARY KEY,
            create_time DATETIME NOT NULL,
            content TEXT NOT NULL,
            alive_turn INT NOT NULL DEFAULT 0,
            status TINYINT(1) NOT NULL DEFAULT 1
            )
        """)
        logger.info(f"创建中期记忆表成功")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS long_term_memory (
            id INT AUTO_INCREMENT PRIMARY KEY,
            create_time DATETIME NOT NULL,
            content TEXT NOT NULL,
            status TINYINT(1) NOT NULL DEFAULT 1
            )
        """)
        logger.info(f"创建长期记忆表成功")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dialog_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            role TEXT NOT NULL,
            type VARCHAR(10) NOT NULL,
            content TEXT NOT NULL,
            duration_seconds FLOAT NOT NULL DEFAULT 0.0,
            create_time DATETIME NOT NULL,
            status TINYINT(1) NOT NULL DEFAULT 1
            )
        """)
        logger.info(f"创建对话历史展示表成功")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_schedule (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date TEXT NOT NULL,
            daily_schedule TEXT NOT NULL
            )
        """)
        logger.info(f"创建每日日程表成功")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS detail_schedule (
            id INT AUTO_INCREMENT PRIMARY KEY,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            activity VARCHAR(20) NOT NULL,
            detail TEXT NOT NULL,
            create_time DATETIME NOT NULL
            )
        """)
        logger.info(f"创建日程细节表成功")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS memes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            path varchar(255) NOT NULL,
            url varchar(255) NOT NULL,
            md5_val varchar(255) NOT NULL,
            try_to_save_vector TINYINT(1) NOT NULL DEFAULT 0,
            vector_status TINYINT(1) NOT NULL DEFAULT 0,
            status TINYINT(1) NOT NULL DEFAULT 1
            )
        """)
        logger.info(f"创建表情包表成功")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS remind (
            id INT AUTO_INCREMENT PRIMARY KEY,
            task_id VARCHAR(255) NOT NULL,
            task_name VARCHAR(255) NOT NULL,
            prompt TEXT NOT NULL,
            create_time DATETIME NOT NULL,
            trigger_time DATETIME NOT NULL,
            status TINYINT(1) NOT NULL DEFAULT 1
            )
        """)
        logger.info(f"创建提醒表成功")

    connection.commit()
except Exception as e:
    logger.error(f"创建库建表失败: {e}")
    connection.rollback()
finally:
    connection.close()


DATABASE_URL = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db']}?charset=utf8mb4"
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(bind=engine)

def get_session() -> Session:
    """获取数据库会话"""
    return SessionLocal()