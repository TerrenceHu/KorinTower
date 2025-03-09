from datetime import date
from loguru import logger

import mysql.connector
from mysql.connector import Error


class UsernameModel:
    def __init__(self, host, user, password, database):
        """
        初始化数据库连接
        """
        try:
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                charset='utf8mb4'
            )
            self.cursor = self.connection.cursor()
        except Error as e:
            logger.error(f"Error connecting to MySQL Database: {e}")

    def add_username(self, username: str, visited_date: date = None) -> bool:
        """
        添加一个新的 username 记录
        """
        if visited_date is None:
            visited_date = date.today()
        try:
            query = """
            INSERT INTO visited_usernames (username, visited_date)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE visited_date = VALUES(visited_date)
            """
            values = (username, visited_date)
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error adding or updating username {username}: {e}")
            self.connection.rollback()
            return False

    def does_username_exist(self, username: str) -> bool:
        """
        检查 username 是否存在于 visited_usernames 表中
        """
        query = "SELECT EXISTS(SELECT 1 FROM visited_usernames WHERE username = %s LIMIT 1)"
        values = (username,)
        result = self._fetch_one(query, values)
        if result is None:
            return False
        return result[0]


    def close_connection(self):
        """
        关闭数据库连接
        """
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            logger.info("Database connection closed")