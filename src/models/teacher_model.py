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

    def add_teacher(self, id: int, username: str,
                    name: str, city_id: int, district_id: str, price: str, price1: str,
                    age: str, height: str, weight: str, measurement: str, service: str,
                    updated_date: date):
        # 开始事务
        self.connection.start_transaction()

        """
        添加一个新的 teacher 记录
        """
        query = '''
        INSERT INTO teachers (
            id, username, name, city_id, district_id, price1p, updated_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s);
        '''
        values = (id, username, name, city_id, district_id, price1, updated_date)
        if not self._execute_query(query, values):
            logger.error(f"Error adding teacher: {id},{username}")
            self.connection.rollback()
            return False
        
        info_query = '''
        INSERT INTO teachers_info (
            id, age, price, height, weight, measurement, service
        ) VALUES (%s, %s, %s, %s, %s, %s, %s);
        '''
        info_values = (id, age, price, height, weight, measurement, service)
        if not self._execute_query(info_query, info_values):
            logger.error(f"Error adding teacher_info: {id}")
            self.connection.rollback()
            return False
        
        # 提交事务
        self.connection.commit()
        return True

    def does_teacher_exist(self, id) -> bool:
        """
        检查 teacher 是否存在
        """
        query = "SELECT EXISTS(SELECT 1 FROM teachers WHERE id = %s LIMIT 1)"
        values = (id,)
        result = self._fetch_one(query, values)
        if result is None:
            return False
        return result[0]

    def get_effective_teachers_by_city(self, city_id):
        """
        获取某城市中所有 teachers 记录
        """
        select_query = "SELECT DISTINCT username, name FROM teachers where status = 0 and city_id = %s"
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
        select_query = "SELECT DISTINCT username, name FROM teachers where status = 0 and district_id = %s"
        values = (district_id,)
        try:
            self.cursor.execute(select_query, values)
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"Error retrieving all teachers of district {district_id}: {e}")

    def get_teacher_by_id(self, id):
        """
        获取指定 id 的 teacher 记录
        """
        select_query = "SELECT * FROM teachers WHERE id = %s;"
        values = (id,)
        result = self._fetch_one(select_query, values)
        return result
    
    def get_teacher_by_username(self, username):
        """
        获取指定 username 的 teacher 记录
        """
        select_query = "SELECT * FROM teachers WHERE username = %s;"
        values = (username,)
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

    def add_report(self, teacher_id: int, channel_id: int, message_id: int, type: int, dt: datetime):
        """
        创建一个新的 report 记录
        """
        query = '''
        INSERT INTO kt.teachers_reports (
            teacher_id, channel_id, message_id, type, dt
        ) VALUES (%s, %s, %s, %s, %s);
        '''
        values = (teacher_id, channel_id, message_id, type, dt)
        if not self._execute_query(query, values):
            logger.error(f"Failed to add report {channel_id},{message_id} for teacher {teacher_id}")

    def get_reports_by_teacher_id(self, teacher_id: int):
        query = '''
        SELECT * FROM kt.teachers_reports WHERE teacher_id = %s;
        '''
        values = (teacher_id,)
        if not self._execute_query(query, values):
            logger.error(f"Failed to get reports by teacher id {teacher_id}")
        
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
