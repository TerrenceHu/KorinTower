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
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
                #self._create_table_if_not_exists()
        except Error as e:
            print(f"Error connecting to MySQL Database: {e}")

    def _create_table_if_not_exists(self):
        """
        创建group表，如果不存在的话
        """
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS groups (
            id INT AUTO_INCREMENT PRIMARY KEY,
            group_id BIGINT UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        try:
            self.cursor.execute(create_table_query)
            self.connection.commit()
        except Error as e:
            print(f"Error creating table: {e}")

    def add_group(self, id: int, name: str):
        """
        添加一个新的群组记录
        """
        insert_query = '''
        INSERT INTO groups (id, name) VALUES (%s, %s);
        '''
        try:
            self.cursor.execute(insert_query, (id, name))
            self.connection.commit()
        except Error as e:
            print(f"Error adding group: {e}")


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


    def get_all_groups(self):
        """
        获取所有群组记录
        :return: 所有群组的列表
        """
        select_query = 'SELECT * FROM groups;'
        try:
            self.cursor.execute(select_query)
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error retrieving groups: {e}")
            return []

    def update_group_name(self, group_id: int, new_name: str):
        """
        更新指定群组的名称
        :param group_id: 要更新的群组ID
        :param new_name: 新的群组名称
        """
        update_query = '''
        UPDATE groups SET name = %s WHERE group_id = %s;
        '''
        try:
            self.cursor.execute(update_query, (new_name, group_id))
            self.connection.commit()
        except Error as e:
            print(f"Error updating group name: {e}")

    def delete_group(self, group_id: int):
        """
        删除指定群组记录
        :param group_id: 要删除的群组ID
        """
        delete_query = '''
        DELETE FROM groups WHERE group_id = %s;
        '''
        try:
            self.cursor.execute(delete_query, (group_id,))
            self.connection.commit()
        except Error as e:
            print(f"Error deleting group: {e}")

    def close_connection(self):
        """
        关闭数据库连接
        """
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()

# 示例用法
if __name__ == "__main__":
    db_manager = GroupModel("rm-wz9682u97cx7e84l1xo.mysql.rds.aliyuncs.com",
                                "korin", "Python4x", "kt")
    db_manager.add_user_to_group(1891648796, 98137104)

    # 添加群组
    #db_manager.add_group(123456789, "Example Group")

    # 获取所有群组
    #groups = db_manager.get_all_groups()
    #print(groups)

    # 更新群组名称
    #db_manager.update_group_name(123456789, "Updated Group Name")

    # 删除群组
    #db_manager.delete_group(123456789)

    # 关闭连接
    db_manager.close_connection()