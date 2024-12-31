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


       
    messages = client.iter_messages(2056779794)
    for message in messages:
        print(message)




if __name__ == "__main__":
    main()
