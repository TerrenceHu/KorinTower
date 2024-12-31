import csv
import pytz
from datetime import date, datetime, timedelta

from telethon.sync import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import User, Channel
from telethon.errors.rpcerrorlist import InviteRequestSentError, UserAlreadyParticipantError
from telethon import utils

from models.channel_model import ChannelModel

from utils.chats import *


class ChannelAgent():
    def __init__(self, client: TelegramClient) -> None:
        self.client = client

        self.db_host = "rm-wz9682u97cx7e84l1xo.mysql.rds.aliyuncs.com"
        self.db_user = "korin"
        self.db_password = "Python4x"
        self.db_database = "kt"
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