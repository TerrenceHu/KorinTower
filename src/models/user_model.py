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

    def get_all_users(self):
        """
        获取所有用户记录
        """
        select_query = 'SELECT * FROM users;'
        try:
            self.cursor.execute(select_query)
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error retrieving users: {e}")
            return []

    def get_user_by_id(self, id):
        """Retrieve a user by their ID."""
        query = "SELECT * FROM users WHERE id = %s"
        values = (id,)
        result = self._fetch_one(query, values)
        return result

    def update_user(self, id, first_name=None, last_name=None, username=None, about=None):
        """
        Update an existing user's information.
        """
        set_clause = []
        values = []

        if first_name is not None:
            set_clause.append("first_name = %s")
            values.append(first_name)
        if last_name is not None:
            set_clause.append("last_name = %s")
            values.append(last_name)
        if username is not None:
            set_clause.append("username = %s")
            values.append(username)
        if about is not None:
            set_clause.append("about = %s")
            values.append(about)

        set_clause_str = ", ".join(set_clause)
        query = f"UPDATE users SET {set_clause_str} WHERE user_id = %s"
        values.append(user_id)

        self._execute_query(query, tuple(values))

    def delete_user(self, user_id):
        """
        删除用户
        """
        query = "DELETE FROM users WHERE user_id = %s"
        values = (user_id,)
        self._execute_query(query, values)

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
