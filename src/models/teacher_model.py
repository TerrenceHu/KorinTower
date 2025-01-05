import logging
from datetime import date, datetime

import mysql.connector
from mysql.connector import Error

logger = logging.getLogger(__name__)

class TeacherModel:
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

    def add_teacher(self, id: int, username: str, title: str, join_request: bool,
                    participants_count: int, updated_on: date):
        """
        添加一个新的 channel 记录
        """
        query = '''
        INSERT INTO channels (id, username, title, join_request, participants_count, updated_on)
        VALUES (%s, %s, %s, %s, %s, %s);
        '''
        values = (id, username, title, join_request, participants_count, updated_on)
        if not self._execute_query(query, values):
            logger.error(f"Error adding channel {id},{username}")

    def does_teacher_exist(self, id) -> bool:
        """
        检查channel是否存在于 channels 表中
        """
        query = "SELECT EXISTS(SELECT 1 FROM channels WHERE id = %s LIMIT 1)"
        values = (id,)
        result = self._fetch_one(query, values)
        if result is None:
            return False
        return result[0]

    def get_teacher_by_id(self, id):
        """Retrieve a channel by ID."""
        select_query = "SELECT * FROM channels WHERE id = %s;"
        values = (id,)
        result = self._fetch_one(select_query, values)
        return result

    def delete_teacher(self, id: int):
        """
        删除指定频道记录
        """
        delete_query = '''
        DELETE FROM channels WHERE id = %s;
        '''
        try:
            self.cursor.execute(delete_query, (id,))
            self.connection.commit()
        except Error as e:
            logger.error(f"Error deleting channel {id}: {e}")

    def _execute_query(self, query, values) -> bool:
        """
        Execute a query with optional parameters.
        """
        try:
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error executing query: {e}")
            return False

    def _fetch_one(self, query, values):
        """
        Fetch a single row from the database.
        """
        try:
            self.cursor.execute(query, values)
            result = self.cursor.fetchone()
            return result
        except Error as e:
            logger.error(f"Error fetching data: {e}")
            return None

    def close_connection(self):
        """
        关闭数据库连接
        """
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
