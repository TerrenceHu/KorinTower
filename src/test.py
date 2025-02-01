from configparser import ConfigParser
from loguru import logger

from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError

from agents.chat_agent import ChatAgent


logger.add(
    "kt.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss}\t{level}\t{name}\t{message}",
    encoding="utf-8"
)

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

    chat_agent = ChatAgent(client, config)
    channel = client.get_entity("lllnnn1106")
    chat_agent.process_channel(channel, '')

    #group_agent = GroupAgent(client, config)
    #group_agent.process_group(group)
    #group = client.get_entity(2470910904)
    #print(group)

    return

if __name__ == "__main__":
    main()
