import logging
import csv
from configparser import ConfigParser
from datetime import date

from telethon.sync import TelegramClient
from telethon.tl.types import Channel

from models.channel_model import ChannelModel
from utils.chats import *


logger = logging.getLogger(__name__)
today_date = date.today()

class ChannelAgent():
    def __init__(self, client: TelegramClient, config: ConfigParser) -> None:
        self.client = client

        self.db_host = config.get('DATABASE', 'db_host')
        self.db_user = config.get('DATABASE', 'db_user')
        self.db_password = config.get('DATABASE', 'db_password')
        self.db_database = config.get('DATABASE', 'db_database')
        self.channel_model = ChannelModel(host=self.db_host, user=self.db_user,
                                          password=self.db_password, database=self.db_database)

    # 抓取Channel消息
    def get_channel_messages(self, channel: Channel) -> bool:
        # 为了控制prompt的token数，优先用pinned消息，再用其他消息
        pinned_messages = []
        candidate_messages = []
        prompt_messages = []
        # 只抓取最早的200条消息进行存储，很可能包含老师的课表信息
        messages = self.client.iter_messages(channel.id, limit=200, reverse=True)
        for message in messages:
            if message.message:
                message_text = message.message.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
                self.channel_model.add_message_to_channel(channel.id, message.id, message_text, message.date)
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

        return True

    def parse_channel_messages(self):
        all_channels = self.channel_model.get_all_channels()
        for channel in all_channels:
            print(f"=========================={channel[0]},{channel[1]},{channel[2]}")
            messages = self.channel_model.get_channel_messages(channel[0])

            # 为了控制prompt的token数，优先用pinned消息，再用其他消息
            pinned_messages = []
            candidate_messages = []
            prompt_messages = []
            for message in messages:
                if message[2]:
                    message_text = message[2].replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
                    #if message.pinned:
                    if False:
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

            # 读取prompt模板文件
            prompt_template_file = 'config/prompt_template.txt'
            try:
                prompt_template = read_prompt_template(prompt_template_file)
            except FileNotFoundError as e:
                logger.error(e)
                continue
            print(prompt_template)
            prompt = prompt_template.format(content=content)
            print(prompt)
