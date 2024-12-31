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

    # 解析Channel消息
    def parse_channel(self, channel: Channel) -> bool:
        messages = self.client.iter_messages(channel.id, limit=100, reverse=True)
        for message in messages:
            if message.message:
                content = message.message.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
                #print(str(message.date) + " " + content + " " + str(message.photo if message.photo else "None"))
                print(content)

    # 解析Channel消息
    def get_channel_messages(self, channel: Channel) -> bool:
        f = open("data/channel_messages.csv", 'a', encoding='utf-8-sig')
        csv_writer = csv.writer(f, delimiter='\t')

        content = []
        # 只抓取最早的200条消息，通常包含老师的课表信息
        messages = self.client.iter_messages(channel.id, limit=200, reverse=True)
        for message in messages:
            message_text = message.message
            if message_text:
                content.append(message_text.replace('\r', ' ').replace('\n', ' ').replace('\t', ' '))
                self.channel_model.add_message_to_channel(channel.id, message.id, message_text, message.date)
        else:
            csv_writer.writerow([str(channel.username), str(channel.title), ";" . join(content), "0"])
            f.close()

        return True