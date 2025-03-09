from loguru import logger
from datetime import date

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

    def add_teacher(self, channel_id: int, channel_username: str,
                    user_id: int, user_username: str,
                    name: str, city_id: int, district_id: str, price: str, price1: str,
                    age: str, height: str, weight: str, measurement: str, service: str,
                    updated_on: date):
        # 开始事务
        self.connection.start_transaction()

        """
        添加一个新的 teacher 记录
        """
        teachers_query = '''
        INSERT INTO teachers (
            channel_id, channel_username, user_id, user_username,
            name, city_id, district_id, price1p, updated_on
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        '''
        teachers_values = (channel_id, channel_username, user_id, user_username,
                           name, city_id, district_id, price1, updated_on)
        if not self._execute_query(teachers_query, teachers_values):
            logger.error(f"Error adding teacher to teachers table: {channel_id},{channel_username},{user_id},{user_username}")
            self.connection.rollback()
            return False
        
        teachers_info_query = '''
        INSERT INTO teachers_info (
            channel_id, age, price, height, weight, measurement, service
        ) VALUES (%s, %s, %s, %s, %s, %s, %s);
        '''
        teachers_info_values = (channel_id, age, price, height, weight, measurement, service)
        if not self._execute_query(teachers_info_query, teachers_info_values):
            logger.error(f"Error adding teacher to teachers_info table: {channel_id},{channel_username},{user_id},{user_username}")
            self.connection.rollback()
            return False
        
        # 提交事务
        self.connection.commit()
        return True

    def does_teacher_exist(self, channel_id) -> bool:
        """
        检查 teacher 是否存在于 teachers 表中
        """
        query = "SELECT EXISTS(SELECT 1 FROM teachers WHERE channel_id = %s LIMIT 1)"
        values = (channel_id,)
        result = self._fetch_one(query, values)
        if result is None:
            return False
        return result[0]

    def get_effective_teachers_by_city(self, city_id):
        """
        获取某城市中所有 teachers 记录
        """
        select_query = "SELECT DISTINCT user_username, name FROM teachers where status = 0 and city_id = %s"
        values = (city_id,)
        try:
            self.cursor.execute(select_query, values)
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"Error retrieving all teachers of city {city_id}: {e}")
    
    def get_effective_teachers_by_district(self, district_id):
        """
        获取某区域中所有 teachers 记录
        """
        select_query = "SELECT DISTINCT user_username, name FROM teachers where status = 0 and district_id = %s"
        values = (district_id,)
        try:
            self.cursor.execute(select_query, values)
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"Error retrieving all teachers of district {district_id}: {e}")

    def get_teacher_by_channel_id(self, channel_id):
        """Retrieve a teacher by channel id"""
        select_query = "SELECT * FROM teachers WHERE channel_id = %s;"
        values = (channel_id,)
        result = self._fetch_one(select_query, values)
        return result
    
    def get_teacher_by_user_username(self, user_username):
        """Retrieve a teacher by user username"""
        select_query = "SELECT * FROM teachers WHERE user_username = %s;"
        values = (user_username,)
        result = self._fetch_one(select_query, values)
        return result
    
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
