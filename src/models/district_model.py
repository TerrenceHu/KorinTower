from loguru import logger

import mysql.connector
from mysql.connector import Error


class DistrictModel:
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

    def get_all_cities(self):
        """
        获取所有
        """
        select_query = "SELECT * FROM districts where pid = 0;"
        try:
            self.cursor.execute(select_query)
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"Error retrieving all channels: {e}")
            return []

    def get_districts_of_city(self, id):
        """
        获取某个城市的所有区县
        """
        select_query = "SELECT * FROM districts where pid = %s;"
        try:
            self.cursor.execute(select_query, (id,))
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"Error retrieving districts of city {id}: {e}")
            return []

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

    def close_connection(self):
        """
        关闭数据库连接
        """
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
