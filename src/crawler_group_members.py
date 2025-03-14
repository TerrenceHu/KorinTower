from configparser import ConfigParser
from loguru import logger

from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError

from agents.group_agent import GroupAgent

logger.add(
    "group_members.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss}\t{level}\t{name}\t{message}",
    encoding="utf-8"
)

def main() -> None:
    # 读取配置
    config = ConfigParser()
    config.read('config/crawler_config.ini')

    username = config.get('TG', 'username')
    phone = config.get('TG', 'phone')
    api_id = int(config.get('TG', 'api_id'))
    api_hash = config.get('TG', 'api_hash')

    # 创建连接
    client = TelegramClient(username, api_id, api_hash)
    client.start()
    logger.info(f"TelegramClient created for {username}")

    # 确认授权
    if not client.is_user_authorized():
        client.send_code_request(phone)
        try:
            client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            client.sign_in(password=input('Password: '))

    # 获取群成员信息，存量，可以每周一次
    group_agent = GroupAgent(client, config)
    #group_agent.get_group_members()


if __name__ == "__main__":
    main()
