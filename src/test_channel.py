from telethon.sync import TelegramClient

import mysql.connector
from mysql.connector import Error

from agents.channel_agent import ChannelAgent
from models.channel_model import ChannelModel
from models.group_model import GroupModel



def main() -> None:
    db_host = "rm-wz9682u97cx7e84l1xo.mysql.rds.aliyuncs.com"
    db_user = "korin"
    db_password = "Python4x"
    db_database = "kt"
    group_model = GroupModel(host=db_host, user=db_user,
                                    password=db_password, database=db_database)
    id = 2010840625
    query = "SELECT EXISTS(SELECT 1 FROM `groups` WHERE id = %s LIMIT 1)"
    values = (id,)
    connection = mysql.connector.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_database,
            )
    cursor = connection.cursor()
    cursor.execute(query, values)
    result = cursor.fetchone()
    print(result)

    '''
    api_id = 25452895
    api_hash = "9054a96cc2c5fe1bff6c2aa2c8a85a95"

    phone = "+8618600874536"
    username = "terrencehu"
    # 创建连接
    client = TelegramClient(username, api_id, api_hash)
    client.start()
    print("Client Created")

    # 确认授权
    if not client.is_user_authorized():
        client.send_code_request(phone)
        try:
            client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            client.sign_in(password=input('Password: '))


    chat_name = "siyaobb"
    try:
        chat = client.get_entity(chat_name)
        print(chat)
    except Exception as e:
        print(f"Failed to get_entity {chat_name}: {e}")
    
    channel_agent = ChannelAgent(client)
    channel_agent.parse_channel(chat)
    '''



if __name__ == "__main__":
    main()
