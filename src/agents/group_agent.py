import logging
import pytz
from configparser import ConfigParser
from datetime import date, datetime, timedelta

from telethon.sync import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import User, Channel
from telethon.errors.rpcerrorlist import InviteRequestSentError, UserAlreadyParticipantError
from telethon import utils

from models.group_model import GroupModel
from models.channel_model import ChannelModel
from models.user_model import UserModel

from agents.channel_agent import ChannelAgent
from utils.chats import *


logger = logging.getLogger(__name__)
today_date = date.today()

class GroupAgent():
    def __init__(self, client: TelegramClient, config: ConfigParser) -> None:
        self.client = client
        self.config = config

        # 群组、频道和用户的数据库模型
        self.db_host = config.get('DATABASE', 'db_host')
        self.db_user = config.get('DATABASE', 'db_user')
        self.db_password = config.get('DATABASE', 'db_password')
        self.db_database = config.get('DATABASE', 'db_database')
        self.user_model = UserModel(host=self.db_host, user=self.db_user,
                                    password=self.db_password, database=self.db_database)
        self.group_model = GroupModel(host=self.db_host, user=self.db_user,
                                      password=self.db_password, database=self.db_database)
        self.channel_model = ChannelModel(host=self.db_host, user=self.db_user,
                                          password=self.db_password, database=self.db_database)

        self.channel_agent = ChannelAgent(client, config)

        # 获取所有群组（数据库中纪录的、上次新加入的）、当前对话中的频道
        for dialog in client.get_dialogs():
            logger.info(f"Get dialog: {dialog.name}")
            if dialog.is_user:
                logger.info(f"Ignore dialog as user: {dialog.name}")
                continue
            elif dialog.is_group:
                self.process_group(dialog.entity)
            elif dialog.is_channel:
                self.process_channel(dialog.entity)

        # 记录已经抓取过的names，减少重复请求
        self.chat_names = {}

    # 获取群组成员，从群组成员的about中获取group或channel
    def get_group_members(self) -> None:
        today_date = date.today()
        for group_item in self.group_model.get_all_groups():
            id, username = group_item[0], group_item[1]
            logger.info(f"get_group_members group: {id},{username}")
            # 因Telegram API限制，无法获取全部群组成员；"aggressive" Does nothing
            try:
                # TODO: 
                # 1. 这里不知道为什么，先get_entity可以减少get_participants失败的情况
                # 2. 需要记录获取成员失败的群，后续二次处理
                if username:
                    group = self.client.get_entity(username)
                members = self.client.get_participants(id, aggressive=True)
            except Exception as e:
                logger.error(f"Failed to get participants of group {id},{username}: {e}")
                continue

            for member in members:
                # 过滤bot、广告号、已经爬过的用户，减少TG请求
                # TODO: 可能用户信息会更新，需要重新爬取
                if member.bot:
                    continue
                if filter_entity_by_title(member.first_name) or filter_entity_by_title(member.last_name):
                    continue
                if member.first_name == "" and member.last_name == "" and member.username == "":
                    continue
                if self.user_model.does_user_exist(member.id):
                    continue

                # 获取用户的info
                try:
                    full_member = self.client(GetFullUserRequest(member))
                except Exception as e:
                    logger.error(f"Failed to GetFullUserRequest {member.id},{member.username}: {e}")
                    continue

                about = full_member.full_user.about
                if about:
                    about = about.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')

                if not self.user_model.does_user_exist(member.id):
                    self.user_model.add_user(member.id, member.username, member.first_name, member.last_name, about)
                    logger.info(f"Add new user to db: {member.id},{member.username}")
                self.group_model.add_user_to_group(id, member.id, today_date)

                # 根据info再次过滤广告号，广告号没有价值且处理麻烦
                if filter_entity_by_info(about):
                    continue

                # 从info中获取新的群组或频道
                chat_names = find_channel(full_member.full_user.about)
                if len(chat_names) < 1:
                    continue
                self.process_chat_names(chat_names)

    # 获取群组消息，从群组消息中获取group或channel
    def get_group_messages(self) -> None:
        today_date = date.today()
        for id, name in self.group_model.get_all_groups():
            today = datetime(today_date.year, today_date.month, today_date.day, tzinfo=pytz.utc)
            yesterday_date = date.today() - timedelta(days=1)
            yesterday = datetime(yesterday_date.year, yesterday_date.month, yesterday_date.day, tzinfo=pytz.utc)

            # offset_date is used to get messages prior to that date
            messages = self.client.iter_messages(id, offset_date=today)

            '''
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
            else:
                f.close()
            '''

    def process_group(self, group: Channel) -> bool:
        logger.info(f"Processing group: {group.id},{group.username},{group.title}")
        # 过滤成员少于1000、广告、已经加入的Group
        # TODO: 判断是否是老师群
        try:
            if group.participants_count != None and group.participants_count < 1000:
                logger.info(f"Too few members in group: {group.id},{group.username},{group.title}")
                return True
            if filter_group_by_title(group.title):
                logger.info(f"Filter ad group: {group.id},{group.username},{group.title}")
                return True
        except Exception as e:
            logger.error(f"Failed to filter group: {group.id}: {e}")
            return False
        
        if self.group_model.does_group_exist(group.id):
            logger.info(f"Already added group: {group.id},{group.username},{group.title}")
        else:
            self.group_model.add_group(group.id, group.username, group.title, group.join_request,
                                       group.participants_count, today_date)
            logger.info(f"Add new group to db: {group.id},{group.username},{group.title}")
        return True

    def process_channel(self, channel: Channel) -> bool:
        logger.info(f"Processing channel: {channel.id},{channel.username},{channel.title}")
        # 过滤广告、已经抓取过的Channel
        if filter_entity_by_title(channel.title):
            logger.info(f"Filter ad channel: {channel.id},{channel.username},{channel.title}")
            return True
        if self.channel_model.does_channel_exist(channel.id):
            logger.info(f"Already added channel: {channel.id},{channel.username},{channel.title}")
        else:
            is_teacher = False
            self.channel_model.add_channel(channel.id, channel.username, channel.title, channel.join_request,
                                           channel.participants_count, today_date, is_teacher)
            logger.info(f"Add new channel to db: {channel.id},{channel.username},{channel.title}")
            self.channel_agent.get_channel_messages(channel)
            #self.channel_agent.parse_channel(channel)
        return True

    def process_chat_names(self, chat_names: list) -> None:
        logger.info(f"Processing chat names: {chat_names}")
        for chat_name in chat_names:
            if chat_name.lower().endswith("bot"):
                continue
            if chat_name in self.chat_names:
                logger.info(f"Already checked chat: {chat_name}")
                continue
            else:
                self.chat_names[chat_name] = 1

            # TODO: 加入 private chat 怎么处理？
            '''
            if chat_name.startswith("+"):
                self.join_private_chat(chat_name)
                continue
            '''

            try:
                chat = self.client.get_entity(chat_name)
            except Exception as e:
                logger.error(f"Failed to get_entity {chat_name}: {e}")
                continue

            # 过滤User
            if isinstance(chat, User):
                logger.info(f"Ignore chat as user: {chat_name}")
                continue

            # 如果是Group
            if chat.megagroup == True:
                self.process_group(chat)
            # 如果是Channel
            else:
                self.process_channel(chat)

    # 加入 group
    def join_group(self, chat: Channel) -> bool:
        try:
            self.client(JoinChannelRequest(chat))
            print(f"Joined group {chat.title}")
            return True
        except UserAlreadyParticipantError as e:
            print(f"You have already joined group: {chat.title}")
            return True
        except InviteRequestSentError as e:
            print(f"Successfully requested to join group: {chat.title}")
        except Exception as e:
            print(f"Failed to join group {chat.title}: {e} {type(e)}")
        return False

    # 加入 private chat
    def join_private_chat(self, chat_name: str) -> bool:
        chat_name = chat_name[1:]
        try:
            self.client(ImportChatInviteRequest(chat_name))
            return True
        except UserAlreadyParticipantError as e:
            print(f"You have already joined private chat: {chat_name}")
            return True
        except InviteRequestSentError as e:
            print(f"Successfully requested to join private channel: {chat_name}")
        except Exception as e:
            print(f"Failed to join private channel {chat_name}: {e} {type(e)}")
        return False