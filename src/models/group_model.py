from datetime import date

import mysql.connector
from mysql.connector import Error

class GroupModel:
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

    def add_group(self, id: int, username: str, title: str, join_request: bool,
                  participants_count: int, updated_on: date):
        """
        添加一个新的群组记录
        """
        query = '''
        INSERT INTO `groups` (id, username, title, join_request, participants_count, updated_on)
        VALUES (%s, %s, %s, %s, %s, %s);
        '''
        values = (id, username, title, join_request, participants_count, updated_on)
        if not self._execute_query(query, values):
            print(f"Error adding group: {id}")

    def does_group_exist(self, id):
        """
        检查group是否存在于 groups 表中
        """
        query = "SELECT EXISTS(SELECT 1 FROM `groups` WHERE id = %s LIMIT 1)"
        values = (id,)
        result = self._fetch_one(query, values)
        return result[0]

    def get_all_groups(self):
        """
        获取所有群组记录
        """
        select_query = 'SELECT * FROM `groups`;'
        try:
            self.cursor.execute(select_query)
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error retrieving groups: {e}")
            return []

    def add_user_to_group(self, group_id: int, user_id: int, updated_on: date):
        """
        将用户添加到群组中
        """
        if self.is_user_in_group(group_id, user_id):
            return

        insert_query = '''
        INSERT INTO group_members (group_id, user_id, updated_on) VALUES (%s, %s, %s);
        '''
        try:
            self.cursor.execute(insert_query, (group_id, user_id, updated_on))
            self.connection.commit()
        except Error as e:
            print(f"Error adding user to group: {e} {group_id} {user_id}")

    def is_user_in_group(self, group_id: int, user_id: int) -> bool:
        """
        检查用户是否已经是群组成员
        """
        query = '''
        SELECT COUNT(*) FROM group_members WHERE group_id = %s AND user_id = %s;
        '''
        try:
            self.cursor.execute(query, (group_id, user_id))
            count = self.cursor.fetchone()[0]
            return count > 0
        except Error as e:
            print(f"Error checking if user exists in group: {e}")
            return False

    def delete_group(self, id: int):
        """
        删除指定群组记录
        """
        delete_query = '''
        DELETE FROM `groups` WHERE id = %s;
        '''
        try:
            self.cursor.execute(delete_query, (id,))
            self.connection.commit()
        except Error as e:
            print(f"Error deleting group: {e}")

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
