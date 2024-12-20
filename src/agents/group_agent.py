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
from utils.teachers import *

# get_input_entity
# FloodWaitError

class GroupAgent():
    def __init__(self, client: TelegramClient) -> None:
        self.client = client
        #me = self.client.get_me()

        
        self.my_users = {}
        self.my_groups = {}
        self.my_channels = {}
        for dialog in client.get_dialogs():
            if dialog.is_user:
                continue
            elif dialog.is_group:
                self.my_groups[dialog.entity.id] = dialog.name
                print(f"groups joined: {dialog.entity.id},{dialog.name}")
            elif dialog.is_channel:
                self.my_channels[dialog.entity.id] = dialog.name
                print(f"channels joined: {dialog.entity.id},{dialog.name}")
        
        self.not_teacher_channels = {}

    # 解析Channel消息
    def parse_channle_messages(self, channel: Channel) -> bool:
        messages = self.client.iter_messages(channel.id)
        for message in messages:
            print(message)
        
        return True
    
    
    def join_channels(self, join_list: list) -> None:
        for username in join_list:
            if username.startswith("+"):
                username = username[1:]
                try:
                    self.client(ImportChatInviteRequest(username[1:]))
                except UserAlreadyParticipantError as e:
                    print(f"You are already a participant of private channel: {username}")
                except InviteRequestSentError as e:
                    print(f"Successfully requested to join private channel: {username}")
                except Exception as e:
                    print(f"Failed to join private channel {username}: {e} {type(e)}")
                continue

            try:
                channel = self.client.get_entity(username)
            except Exception as e:
                print(f"Failed to get_entity {username}: {e}")
                continue

            # 如果是User或已经加入的Channel和Group，跳过
            if isinstance(channel, User):
                print(f"{username} is a User")
                continue
            #if channel.id in self.my_groups or channel.id in self.my_channels:
            #    print(f"Already joined {username}")
            #    continue
            if filter_ad_user(channel.title):
                print(f"{username} is a ad User")
                continue

            if channel.megagroup == True:
                # 如果是Group，过滤条件：成员少于100
                if channel.participants_count != None and channel.participants_count < 100:
                    print(f"Too few members in group: {username}")
                    continue
                try:
                    self.client(JoinChannelRequest(channel))
                    self.my_groups[channel.id] = channel.title
                    print(f"Joined group {channel.title}")
                except UserAlreadyParticipantError as e:
                    print(f"You are already a participant of group: {username}")
                except InviteRequestSentError as e:
                    print(f"Successfully requested to join group: {username}")
                except Exception as e:
                    print(f"Failed to join group {username}: {e} {type(e)}")
                    print(channel)
            else:
                # 如果是Channel，过滤条件：成员少于50
                if channel.participants_count != None and channel.participants_count < 50:
                    print(f"Too few members in channel: {username}")
                    continue
                # 如果之前检测过不是老师，就过滤
                if channel.id in self.not_teacher_channels:
                    continue
                try:
                    self.client(JoinChannelRequest(channel))
                    # 加入后判断是否是老师的Channel，不是就退出
                    is_teacher = self.parse_channle_messages(channel)
                    if is_teacher:
                        self.my_channels[channel.id] = channel.title
                        # TODO:写入文件或者数据库
                        print(f"Joined channel {channel.title}")
                    else:
                        self.not_teacher_channels[channel.id] = channel.title
                except InviteRequestSentError as e:
                    print(f"Successfully requested to join channel: {username}")
                except UserAlreadyParticipantError as e:
                    print(f"You are already a participant of channel: {username}")
                except Exception as e:
                    print(f"Failed to join channel {username}: {e} {type(e)}")
                    print(channel)
            

    # 获取群组成员，从群组成员的about中获取group或channel
    def get_group_members(self) -> None:
        for id, name in self.my_groups.items():
            # 因Telegram API限制，无法获取全部群组成员；"aggressive" Does nothing
            members = self.client.iter_participants(id, aggressive=True)

            # TODO:写入文件或者数据库
            yesterday_date = date.today() - timedelta(days=1)
            f = open("data/members.%s.%s" % (name, str(yesterday_date)), 'w', encoding='utf-8-sig')
            csv_writer = csv.writer(f)
            csv_writer.writerow(["first_name", "username", "id", "about", "others"])

            for member in members:
                if member.id in self.my_users:
                    continue
                if member.bot:
                    continue
                if filter_ad_user(member.first_name) or filter_ad_user(member.last_name):
                    continue
                full_member = self.client(GetFullUserRequest(member))
                print(member)
                print(full_member.full_user)
                self.my_users[member.id] = full_member.full_user.about
                channel_usernames = find_channel(full_member.full_user.about)
                if len(channel_usernames) < 1:
                    continue
                self.join_channels(channel_usernames)
                            
                csv_writer.writerow([str(full_member.users[0].first_name),
                                    str(full_member.users[0].username),
                                    str(full_member.full_user.id),
                                    str(full_member.full_user.about).replace('\r', '').replace('\n', '').replace('\t', ''),
                                    ":".join(channel_usernames)]
                                    )
            f.close()

    # 获取群组消息，从群组消息中获取group或channel
    def get_group_messages(self) -> None:
        for id, name in self.my_groups.items():
            today_date = date.today()
            today = datetime(today_date.year, today_date.month, today_date.day, tzinfo=pytz.utc)
            yesterday_date = date.today() - timedelta(days=1)
            yesterday = datetime(yesterday_date.year, yesterday_date.month, yesterday_date.day, tzinfo=pytz.utc)

            # offset_date is used to get messages prior to that date
            messages = self.client.iter_messages(id, offset_date=today)
        
            # TODO:写入文件或者数据库
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
