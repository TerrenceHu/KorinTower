from telethon.sync import TelegramClient

from agents.channel_agent import ChannelAgent
from models.channel_model import ChannelModel


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


    chat_name = "siyaobb"
    try:
        chat = client.get_entity(chat_name)
        print(chat)
    except Exception as e:
        print(f"Failed to get_entity {chat_name}: {e}")
    
    channel_agent = ChannelAgent(client)
    channel_agent.parse_channel(chat)




if __name__ == "__main__":
    main()
