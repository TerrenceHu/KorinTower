from datetime import date, datetime
from loguru import logger

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
                charset='utf8mb4'
            )
            self.cursor = self.connection.cursor()
        except Error as e:
            logger.error(f"Error connecting to MySQL Database: {e}")

    def add_channel(self, id: int, username: str, title: str, about: str, updated_on: date):
        """
        添加一个新的 channel 记录
        """
        query = '''
        INSERT INTO channels (id, username, title, about, updated_on)
        VALUES (%s, %s, %s, %s, %s);
        '''
        values = (id, username, title, about, updated_on)
        if not self._execute_query(query, values):
            logger.error(f"Error adding channel {id},{username}")

    def does_channel_exist(self, id) -> bool:
        """
        检查channel是否存在于 channels 表中
        """
        query = "SELECT EXISTS(SELECT 1 FROM channels WHERE id = %s LIMIT 1)"
        values = (id,)
        result = self._fetch_one(query, values)
        if result is None:
            return False
        return result[0]

    def get_all_channels(self):
        """
        获取所有频道记录
        """
        select_query = "SELECT * FROM channels;"
        try:
            self.cursor.execute(select_query)
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"Error retrieving all channels: {e}")
            return []
        
    def get_channel_by_id(self, id):
        """Retrieve a channel by ID."""
        select_query = "SELECT * FROM channels WHERE id = %s;"
        values = (id,)
        result = self._fetch_one(select_query, values)
        return result

    def add_message_to_channel(self, channel_id: int, message_id: int, message: str,
                               pinned: bool, comments: bool, replies: int,
                               reactions: int, views: int, dt: datetime):
        """
        将消息添加到渠道中
        """
        if self.is_message_in_channel(channel_id, message_id):
            return

        insert_query = '''
        INSERT INTO channel_messages (channel_id, message_id, message, pinned, comments, replies, reactions, views, dt)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        '''
        try:
            self.cursor.execute(insert_query, (channel_id, message_id, message, pinned, comments, replies, reactions, views, dt))
            self.connection.commit()
        except Error as e:
            logger.error(f"Error adding message to channel {channel_id},{message_id}: {e}")

    def get_channel_messages(self, channel_id: int):
        """
        获取渠道的消息
        """        
        select_query = "SELECT * FROM channel_messages WHERE channel_id = %s;"
        try:
            self.cursor.execute(select_query, (channel_id,))
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"Error retrieving all messages for channel {channel_id}: {e}")
            return []
        
    def is_message_in_channel(self, channel_id: int, message_id: int) -> bool:
        """
        检查渠道的消息是否已经记录
        """
        query = '''
        SELECT COUNT(*) FROM channel_messages WHERE channel_id = %s AND message_id = %s;
        '''
        try:
            self.cursor.execute(query, (channel_id, message_id))
            count = self.cursor.fetchone()[0]
            return count > 0
        except Error as e:
            logger.error(f"Error checking if message exists in channel {channel_id},{message_id}: {e}")
            return False

    def update_channel(self, channel_id: int, username: str, title: str,
                       participants_count: int, updated_on: date):
        """
        更新指定频道
        """
        update_query = '''
        UPDATE channels SET username = %s, title = %s, participants_count = %s, updated_on = %s WHERE id = %s;
        '''
        values = (username, title, participants_count, updated_on, channel_id)
        return self._execute_query(update_query, values)
        
    def update_channel_type(self, channel_id: int, type: int) -> bool:
        """
        更新指定频道的 type 字段
        """
        update_query = '''
        UPDATE channels SET type = %s WHERE id = %s;
        '''
        values = (type, channel_id)
        return self._execute_query(update_query, values)
    
    def update_channel_status(self, channel_id: int, status: int) -> bool:
        """
        更新指定频道的 status 字段
        """
        update_query = '''
        UPDATE channels SET status = %s WHERE id = %s;
        '''
        values = (status, channel_id)
        return self._execute_query(update_query, values)
    
    def increment_retries(self, channel_id: int) -> bool:
        """
        增加指定频道的 retries 字段值
        """
        update_query = '''
        UPDATE channels SET retries = retries + 1 WHERE id = %s;
        '''
        values = (channel_id,)
        return self._execute_query(update_query, values)

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
