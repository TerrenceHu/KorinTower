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

# get_input_entity
# FloodWaitError

class GroupAgent():
    def __init__(self, client: TelegramClient) -> None:
        self.client = client

        self.chat_groups = {}
        self.my_channels = {}
        for dialog in client.get_dialogs():
            if dialog.is_user:
                continue
            elif dialog.is_group:
                self.chat_groups[dialog.entity.id] = dialog.name
                #print(f"groups joined: {dialog.entity.id},{dialog.name}")
            elif dialog.is_channel:
                self.my_channels[dialog.entity.id] = dialog.name
                #print(f"channels joined: {dialog.entity.id},{dialog.name}")
        
        self.db_host = "rm-wz9682u97cx7e84l1xo.mysql.rds.aliyuncs.com"
        self.db_user = "korin"
        self.db_password = "Python4x"
        self.db_database = "kt"
        self.group_model = GroupModel(host=self.db_host, user=self.db_user,
                                        password=self.db_password, database=self.db_database)
        self.user_model = UserModel(host=self.db_host, user=self.db_user,
                                        password=self.db_password, database=self.db_database)

        self.not_teacher_channels = {}
    

    # 获取群组成员，从群组成员的about中获取group或channel
    def get_group_members(self) -> None:
        today_date = date.today()
        for id, name in self.chat_groups.items():
            # 因Telegram API限制，无法获取全部群组成员；"aggressive" Does nothing
            members = self.client.iter_participants(id, aggressive=True)
            for member in members:
                # 过滤bot、广告号、已经爬过的用户，减少TG请求
                # TODO: 可能用户信息会更新，需要重新爬取
                if member.bot:
                    continue
                if filter_ad_user_by_name(member.first_name) or filter_ad_user_by_name(member.last_name):
                    continue
                if self.user_model.dose_user_exist(member.id):
                    continue
                if member.first_name == "" and member.last_name == "" and member.username == "":
                    continue
                
                full_member = self.client(GetFullUserRequest(member))
                about = full_member.full_user.about
                if about:
                    about = about.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
                if filter_ad_user_by_info(about):
                    continue

                self.user_model.add_user(member.id, member.username, 
                                            member.first_name, member.last_name, about)
                self.group_model.add_user_to_group(id, member.id, today_date)

                chat_names = find_channel(full_member.full_user.about)
                if len(chat_names) < 1:
                    continue
                self.process_chat_names(chat_names)

    # 获取群组消息，从群组消息中获取group或channel
    def get_group_messages(self) -> None:
        today_date = date.today()
        for id, name in self.chat_groups.items():
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


    # 加入 private chat
    def join_private_chat(self, chat_name: str) -> None:
        chat_name = chat_name[1:]
        try:
            self.client(ImportChatInviteRequest(chat_name))
        except UserAlreadyParticipantError as e:
            print(f"You have already joined private chat: {chat_name}")
        except InviteRequestSentError as e:
            print(f"Successfully requested to join private channel: {chat_name}")
        except Exception as e:
            print(f"Failed to join private channel {chat_name}: {e} {type(e)}")

    # 加入 group
    def join_group(self, chat) -> bool:
        try:
            self.client(JoinChannelRequest(chat))
            self.chat_groups[chat.id] = chat.title
            print(f"Joined group {chat.title}")
            return True
        except UserAlreadyParticipantError as e:
            print(f"You have already joined group: {chat.title}")
        except InviteRequestSentError as e:
            print(f"Successfully requested to join group: {chat.title}")
        except Exception as e:
            print(f"Failed to join group {chat.title}: {e} {type(e)}")
        return False


    # 加入 channel
    def join_channel(self, chat: Channel) -> bool:
        try:
            self.client(JoinChannelRequest(chat))
            # 加入后判断是否是老师的Channel，不是就退出
            #is_teacher = self.parse_channle_messages(channel)
            if False:
                self.my_channels[channel.id] = channel.title
                # TODO:写入文件或者数据库
                print(f"Joined channel {channel.title}")
            else:
                self.not_teacher_channels[channel.id] = channel.title
            return True
        except InviteRequestSentError as e:
            print(f"Successfully requested to join channel: {username}")
        except UserAlreadyParticipantError as e:
            print(f"You are already a participant of channel: {username}")
        except Exception as e:
            print(f"Failed to join channel {username}: {e} {type(e)}")
        return False
    

    def process_chat_names(self, chat_names: list) -> None:
        for chat_name in chat_names:
            if chat_name.startswith("+"):
                self.join_private_chat(chat_name)
                continue

            try:
                chat = self.client.get_entity(chat_name)
            except Exception as e:
                print(f"Failed to get_entity {chat_name}: {e}")
                continue
            print(chat)

            # 过滤User、广告号
            if isinstance(chat, User):
                print(f"{chat_name} is a User")
                continue
            if filter_ad_user_by_name(chat.title):
                print(f"{chat_name} is a ad User")
                continue
            # 过滤已经加入的Channel/Group
            #if chat.id in self.chat_groups or chat.id in self.my_channels:
            #    print(f"Already joined {chat_name}")
            #    continue
            
            # 如果是Group
            if chat.megagroup == True:
                # 过滤条件：成员少于100
                if chat.participants_count != None and chat.participants_count < 100:
                    print(f"Too few members in group: {chat_name}")
                    continue
                self.join_group(chat)
            # 如果是Channel
            else:
                # 过滤条件：成员少于50
                if chat.participants_count != None and chat.participants_count < 50:
                    print(f"Too few members in channel: {chat_name}")
                    continue
                # 如果之前检测过不是老师，就过滤
                if chat.id in self.not_teacher_channels:
                    continue


    # 解析Channel消息
    def parse_channle_messages(self, channel: Channel) -> bool:
        messages = self.client.iter_messages(channel.id)
        for message in messages:
            print(message)
        
        return True