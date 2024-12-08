import logging
import configparser
import socks

from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError

from agents.group import GroupAgent

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


api_id = 25452895
api_hash = "9054a96cc2c5fe1bff6c2aa2c8a85a95"

phone = "+8618600874536"
username = "terrencehu"

def main() -> None:
    # 创建连接
    client = TelegramClient(username, api_id, api_hash)
    client.start()
    logger.info("Client Created")

    # 确认授权
    if not client.is_user_authorized():
        client.send_code_request(phone)
        try:
            client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            client.sign_in(password=input('Password: '))

    group_agent = GroupAgent(client)
    # 获取群成员信息，存量，可以每个月一次
    group_agent.get_group_members()
    # 获取群消息，增量，每天一次
    #group_agent.get_group_messages()

if __name__ == "__main__":
    main()
