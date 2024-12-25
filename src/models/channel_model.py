from datetime import date

import mysql.connector
from mysql.connector import Error

class ChannelModel:
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
            )
            self.cursor = self.connection.cursor()
        except Error as e:
            print(f"Error connecting to MySQL Database: {e}")

    def add_channel(self, id: int, title: str, username: str, is_teacher: bool):
        """
        添加一个新的 channel 记录
        """
        query = '''
        INSERT INTO channels (id, title, username, is_teacher) VALUES (%s, %s, %s, %s);
        '''
        values = (id, title, username, is_teacher)
        if not self._execute_query(query, values):
            print(f"Error adding channel: {id}")

    def does_channel_exist(self, id):
        """
        检查channel是否存在于 channels 表中
        """
        query = "SELECT EXISTS(SELECT 1 FROM channels WHERE id = %s LIMIT 1)"
        values = (id,)
        result = self._fetch_one(query, values)
        return result[0]

    def get_all_channels(self):
        """
        获取所有频道记录
        """
        select_query = 'SELECT * FROM channels;'
        try:
            self.cursor.execute(select_query)
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error retrieving channels: {e}")
            return []

    def delete_channel(self, id: int):
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
            print(f"Error deleting channel: {e}")

    def _execute_query(self, query, values) -> bool:
        """
        Execute a query with optional parameters.
        """
        try:
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error executing query: {e}")
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
            print(f"Error fetching data: {e}")
            return None

    def close_connection(self):
        """
        关闭数据库连接
        """
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
