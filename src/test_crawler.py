from configparser import ConfigParser
from loguru import logger

from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError

from agents.group_agent import GroupAgent


logger.add(
    "kt.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss}\t{level}\t{name}\t{message}",
    encoding="utf-8"
)

def test_group(client: TelegramClient, config: ConfigParser) -> None:
    group_agent = GroupAgent(client, config)
    group = client.get_entity("Benchixiuche168")
    group_agent.process_group(group)

def test_channel(client: TelegramClient, config: ConfigParser) -> None:
    group_agent = GroupAgent(client, config)
    channel = client.get_entity("Fde123jilu")
    teacher = group_agent.process_channel(channel, '')

def main() -> None:
    # 读取配置
    config = ConfigParser()
    config.read('config/kt_config.ini')

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

    test_channel(client, config)
    #test_group(client, config)

    '''
    source_channel_username = "yilantingfeng123"
    target_channel_username = "terrencemmw"
    messages = client.get_messages(source_channel_username, limit=100)
    combined_message = ""
    for message in messages:
        print(message)
        combined_message += f"{message.message}\n\n"
    #client.send_message(target_channel_username, combined_message)
    '''
    return

if __name__ == "__main__":
    main()
