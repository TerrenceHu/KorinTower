from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError

import mysql.connector
from mysql.connector import Error

from models.group_model import GroupModel
from models.channel_model import ChannelModel
from models.user_model import UserModel

from agents.channel_agent import ChannelAgent

def main() -> None:
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

    group = client.get_entity("SZchujifuli")
    #print(group)
    # 因Telegram API限制，无法获取全部群组成员；"aggressive" Does nothing
    members = client.get_participants(1524789233, aggressive=True)

    print(len(members))
    for member in members:
       print(member)
       
    #messages = client.iter_messages(2328524670)
    #for message in messages:
    #    print(message)
    
    '''
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
