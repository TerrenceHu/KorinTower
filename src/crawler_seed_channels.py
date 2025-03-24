from configparser import ConfigParser
from loguru import logger

from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError

from agents.group_agent import GroupAgent

logger.add(
    "logs/crawler_seed_channels.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss}\t{level}\t{name}\t{function}\t{message}",
    encoding="utf-8"
)

def init_client(config: ConfigParser):
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
    return client

def read_seed_channels(file_path: str):
    channels = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:
                city, username, status = line.split(',')
                if int(status) == 1:
                    continue
                channels.append((city, username))
    return channels

def main() -> None:
    # 读取配置
    config = ConfigParser()
    config.read('config/crawler_config.ini')

    # 初始化客户端
    client = init_client(config)

    # 创建 GroupAgent 实例
    group_agent = GroupAgent(client, config)

    seed_channels = read_seed_channels('config/seed_channels.txt')
    for city, username in seed_channels:
        logger.info(f"Crawling channel {username} in city {city}")
        try:
            channel = client.get_entity(username)
            group_agent.process_channel(channel, city)
        except Exception as e:
            logger.error(f"Failed to process channel {username} in city {city}: {e}")

if __name__ == "__main__":
    main()
