from configparser import ConfigParser
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError

from agents.channel_agent import ChannelAgent


def main() -> None:
    # 读取配置
    config = ConfigParser()
    config.read('config/config.ini')

    username = config.get('TG', 'username')
    phone = config.get('TG', 'phone')
    api_id = int(config.get('TG', 'api_id'))
    api_hash = config.get('TG', 'api_hash')

    # 创建连接
    client = TelegramClient(username, api_id, api_hash)
    client.start()
    print(f"TelegramClient created for {username}")

    # 确认授权
    if not client.is_user_authorized():
        client.send_code_request(phone)
        try:
            client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            client.sign_in(password=input('Password: '))

    channel_agent = ChannelAgent(client, config)
    channel = client.get_entity(1635803135)
    print(channel)
    #channel_agent.get_channel_messages(channel)

    return

if __name__ == "__main__":
    main()
