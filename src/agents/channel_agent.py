import json
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

from models.group_model import GroupModel
from models.user_model import UserModel

from utils.teachers import *


class ChannelAgent():
    def __init__(self, client: TelegramClient) -> None:
        self.client = client

    # 解析Channel消息
    def parse_channel(self, channel: Channel) -> bool:
        messages = self.client.iter_messages(channel.id)
        for message in messages:
            if message.message:
                content = message.message.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
                #print(str(message.date) + " " + content + " " + str(message.photo if message.photo else "None"))
                print(content)
                f = open("data/%s.%s.messages" % (name, str(yesterday_date)), 'w', encoding='utf-8-sig')
            csv_writer = csv.writer(f)
            csv_writer.writerow(["date", "sender", "message"])

            for message in messages:
                if message.date <= yesterday:
                    break
                csv_writer.writerow([str(message.date),
                                    str(utils.get_display_name(message.sender)),
                                    str(message.message).replace('\r', '').replace('\n', '').replace('\t', '')]
                                    )
            f.close()


        return True