from loguru import logger
from datetime import date, datetime

import mysql.connector
from mysql.connector import Error

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
    def add_teacher(self, id: int, username: str, name: str, city: str, district: str, age: str, price: str,
                    height: str, weight: str, measurement: str, service: str, status: int, updated_on: date):
        """
        添加一个新的 teacher 记录
        """
        query = '''
        INSERT INTO teachers (id, username, name, city, district, age, price, height, weight, measurement, service, status, updated_on)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        '''
        values = (id, username, name, city, district, age, price, height, weight, measurement, service, status, updated_on)
        if not self._execute_query(query, values):
            logger.error(f"Error adding teacher {id},{username},{name}")

    def does_teacher_exist(self, id) -> bool:
        """
        检查 teacher 是否存在于 teachers 表中
        """
        query = "SELECT EXISTS(SELECT 1 FROM teachers WHERE id = %s LIMIT 1)"
        values = (id,)
        result = self._fetch_one(query, values)
        if result is None:
            return False
        return result[0]

    def get_all_teachers(self):
        """
        获取所有 teachers 表中的记录
        """
        select_query = "SELECT * FROM teachers;"
        try:
            self.cursor.execute(select_query)
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"Error retrieving all teachers: {e}")
            return []
        
    def get_teacher_by_id(self, id):
        """Retrieve a teacher by ID."""
        select_query = "SELECT * FROM teachers WHERE id = %s;"
        values = (id,)
        result = self._fetch_one(select_query, values)
        return result

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
    
    def delete_teacher(self, id: int):
        """
        删除指定 teacher 记录
        """
        delete_query = '''
        DELETE FROM teachers WHERE id = %s;
        '''
        try:
            self.cursor.execute(delete_query, (id,))
            self.connection.commit()
        except Error as e:
            logger.error(f"Error deleting teacher {id}: {e}")

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
