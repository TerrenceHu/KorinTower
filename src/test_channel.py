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


    pinned_messages = []
    candidate_messages = []
    prompt_messages = []
    messages = client.iter_messages(2056779794, limit=200, reverse=True)
    for message in messages:
        if message.message:
            message_text = message.message.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
            if message.pinned:
                pinned_messages.append(message_text)
                print(message_text)
            else:
                candidate_messages.append(message_text)
    content_len = 0
    for message_text in pinned_messages:
        if content_len >= 5000:
            break
        prompt_messages.append(message_text)
        content_len += len(message_text)
    for message_text in candidate_messages:
        if content_len >= 5000:
            break
        prompt_messages.append(message_text)
        content_len += len(message_text)

    content = ";".join(prompt_messages)

    print(content)

    return


if __name__ == "__main__":
    main()
