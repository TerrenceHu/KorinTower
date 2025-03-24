from datetime import date
from loguru import logger

import mysql.connector
from mysql.connector import Error

class UserModel:
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
            print(f"Error connecting to MySQL Database: {e}")

    def add_user(self, id, username, first_name, last_name, about):
        """
        添加一个新的用户记录
        """
        query = '''
        INSERT INTO users (id, username, first_name, last_name, about)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        id = VALUES(id),
        username = VALUES(username),
        first_name = VALUES(first_name),
        last_name = VALUES(last_name),
        about = VALUES(about)
        '''
        values = (id, username, first_name, last_name, about)
        if not self._execute_query(query, values):
            print(f"Error adding user: {id}")

    def does_user_exist(self, id):
        """
        检查用户是否存在于 users 表中
        """
        query = "SELECT EXISTS(SELECT 1 FROM users WHERE id = %s LIMIT 1)"
        values = (id,)
        result = self._fetch_one(query, values)
        return result[0]

    def get_user_by_id(self, id):
        """Retrieve a user by ID."""
        query = "SELECT * FROM users WHERE id = %s"
        values = (id,)
        result = self._fetch_one(query, values)
        return result

    def delete_user(self, user_id):
        """
        删除用户
        """
        query = "DELETE FROM users WHERE user_id = %s"
        values = (user_id,)
        self._execute_query(query, values)
    
    def is_channel_on_user(self, user_id: int, channel_id: int) -> bool:
        """
        检查 channel 是否在 user 上
        """
        query = '''
        SELECT COUNT(*) FROM user_channels WHERE user_id = %s AND channel_id = %s;
        '''
        try:
            self.cursor.execute(query, (user_id, channel_id))
            count = self.cursor.fetchone()[0]
            return count > 0
        except Error as e:
            print(f"Error checking if channel exists on user: {e}")
            return False

    def add_channel_on_user(self, user_id: int, channel_id: int, updated_date: date):
        """
        将 channel 添加到 user 上
        """
        if self.is_channel_on_user(user_id, channel_id):
            return

        insert_query = '''
        INSERT INTO user_channels (user_id, channel_id, updated_date) VALUES (%s, %s, %s);
        '''
        try:
            self.cursor.execute(insert_query, (user_id, channel_id, updated_date))
            self.connection.commit()
        except Error as e:
            print(f"Error adding channel on user: {e} {user_id} {channel_id}")
    
    def get_channels_of_user(self, user_id: int) -> list:
        """
        获取 user 的所有 channel
        """
        query = '''
        SELECT channel_id FROM user_channels WHERE user_id = %s;
        '''
        try:
            self.cursor.execute(query, (user_id,))
            results = self.cursor.fetchall()
            channel_ids = [result[0] for result in results]
            return channel_ids
        except Error as e:
            print(f"Error fetching channels of user: {e} {user_id}")
            return []

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
