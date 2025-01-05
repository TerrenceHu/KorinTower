import logging
from configparser import ConfigParser

from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError

from agents.group_agent import GroupAgent
from agents.channel_agent import ChannelAgent



logging.basicConfig(
    format="%(asctime)s\t%(levelname)s\t%(name)s\t%(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("kt.log")
    ]
)
logger = logging.getLogger(__name__)

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
    logger.info(f"TelegramClient created for {username}")

    # 确认授权
    if not client.is_user_authorized():
        client.send_code_request(phone)
        try:
            client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            client.sign_in(password=input('Password: '))

    #@group_agent = GroupAgent(client, config)
    # 获取群成员信息，存量，可以每个月一次
    #group_agent.get_group_members()
    # 获取群消息，增量，每天一次
    #group_agent.get_group_messages()

    channel_agent = ChannelAgent(client, config)
    channel_agent.update_channels()
    #channel_agent.update_channel(1619393751)

if __name__ == "__main__":
    main()
