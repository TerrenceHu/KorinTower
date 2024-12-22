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

from agents.channel_agent import ChannelAgent

from models.group_model import GroupModel
from models.channel_model import ChannelModel
from models.user_model import UserModel

from utils.teachers import *

# get_input_entity
# FloodWaitError

class GroupAgent():
    def __init__(self, client: TelegramClient) -> None:
        self.client = client

        # 获取当前对话中的群组和频道
        self.chat_groups = {}
        self.chat_channels = {}
        for dialog in client.get_dialogs():
            if dialog.is_user:
                continue
            elif dialog.is_group:
                self.chat_groups[dialog.entity.id] = dialog.name
                #print(f"groups joined: {dialog.entity.id},{dialog.name}")
            elif dialog.is_channel:
                self.chat_channels[dialog.entity.id] = dialog.name
                #print(f"channels joined: {dialog.entity.id},{dialog.name}")
        
        # 群组、频道和用户的数据库模型
        self.db_host = "rm-wz9682u97cx7e84l1xo.mysql.rds.aliyuncs.com"
        self.db_user = "korin"
        self.db_password = "Python4x"
        self.db_database = "kt"
        self.group_model = GroupModel(host=self.db_host, user=self.db_user,
                                        password=self.db_password, database=self.db_database)
        self.channel_model = ChannelModel(host=self.db_host, user=self.db_user,
                                        password=self.db_password, database=self.db_database)
        self.user_model = UserModel(host=self.db_host, user=self.db_user,
                                        password=self.db_password, database=self.db_database)

        # 记录已经抓取过的names，减少重复请求
        self.chat_names = {}

        self.channel_agent = ChannelAgent(client)
    

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
                if member.first_name == "" and member.last_name == "" and member.username == "":
                    continue
                if self.user_model.check_user_exist(member.id):
                    continue
                
                # 获取用户的info
                full_member = self.client(GetFullUserRequest(member))
                about = full_member.full_user.about
                if about:
                    about = about.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')

                self.user_model.add_user(member.id, member.username, 
                                            member.first_name, member.last_name, about)
                self.group_model.add_user_to_group(id, member.id, today_date)

                # 根据info再次过滤广告号，广告号没有价值且处理麻烦
                if filter_ad_user_by_info(about):
                    continue
                    
                # 从info中获取新的群组或频道
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
    def join_group(self, chat: Channel) -> bool:
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
            print(f"Joined channel {chat.title}")
            return True
        except UserAlreadyParticipantError as e:
            print(f"You are already a participant of channel: {chat.title}")
        except InviteRequestSentError as e:
            print(f"Successfully requested to join channel: {chat.title}")
        except Exception as e:
            print(f"Failed to join channel {chat.title}: {e} {type(e)}")
        return False


    def process_chat_names(self, chat_names: list) -> None:
        for chat_name in chat_names:
            if chat_name in self.chat_names:
                print(f"Already checked chat: {chat_name}")
                continue
            else:
                self.chat_names[chat_name] = 1

            # TODO: 加入 private chat 怎么处理？
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
            
            # 如果是Group
            if chat.megagroup == True:
                # 过滤成员少于100、已经加入的Group
                if chat.participants_count != None and chat.participants_count < 100:
                    print(f"Too few members in group: {chat_name}")
                    continue
                if self.group_model.check_group_exist(chat.id):
                    print(f"Already checked group: {chat_name}")
                    continue
                self.join_group(chat)
            # 如果是Channel
            else:
                # 过滤已经加入的Channel
                if self.channel_model.check_channel_exist(chat.id):
                    print(f"Already checked channel: {chat_name}")
                    continue
                is_teacher = False
                if self.join_channel(chat):
                    self.channel_model.add_channel(chat.id, chat.title, chat.username, is_teacher)
                    self.channel_agent.parse_channel(chat)
