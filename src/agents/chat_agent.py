import pytz
import json
from datetime import date, datetime, timedelta
from configparser import ConfigParser
from loguru import logger

from telethon.sync import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import User, Channel, ChannelForbidden
from telethon.errors.rpcerrorlist import InviteRequestSentError, UserAlreadyParticipantError

from globals import *
from utils.chats import *
from agents.group_agent import GroupAgent
from agents.channel_agent import ChannelAgent
from models.group_model import GroupModel
from models.channel_model import ChannelModel
from models.teacher_model import TeacherModel
from models.user_model import UserModel

today_date = date.today()

class ChatAgent():
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
        self.teacher_model = TeacherModel(host=self.db_host, user=self.db_user,
                                          password=self.db_password, database=self.db_database)

        self.group_agent = GroupAgent(client, config)
        self.channel_agent = ChannelAgent(client, config)

        # 获取所有群组（数据库中纪录的、上次新加入的）、当前对话中的频道
        for dialog in client.get_dialogs():
            logger.info(f"Get dialog: {dialog.name}")
            if dialog.is_group:
                self.group_agent.process_group(dialog.entity)

    # 获取群组成员，从群组成员的 about 中获取 group 或 channel
    def get_group_members(self) -> None:
        for group_item in self.group_model.get_all_groups():
            # 过滤失效的 group
            if group_item[5] < 0:
                continue

            id, username, title = group_item[0:3]
            logger.info(f"Get members for group {id},{username},{title}")
            # TODO: 这里不知道为什么，先 get_entity 可以减少 get_participants 失败的情况
            try:
                group = self.client.get_entity(id)
            except Exception as e:
                logger.error(f"Failed to get group {id},{username},{title} by id: {e}")
                try:
                    if username is not None:
                        group = self.client.get_entity(username)
                        if isinstance(group, ChannelForbidden):
                            logger.error(f"Group {id},{username},{title} is forbidden")
                            raise(e)
                        # TODO: 通过 username 可能获得一个新的 group？
                        if group.id != id:
                            logger.error(f"Group {id},{username},{title} is not the same as {group.id}")
                            if not self.group_model.does_group_exist(group.id):
                                self.group_model.add_group(group.id, group.username, group.title, group.participants_count, today_date)
                                logger.info(f"Add new group {group.id},{group.username},{group.title} to db")
                            raise(e)
                    else:
                        raise(e)
                except Exception as e:
                    logger.error(f"Failed to get group {id},{username},{title} by username: {e}")
                    self.group_model.update_group_status(id, -1)
                    continue

            # group 的 username 和 title 可能会变化，需要更新
            if group.username != group_item[1] or group.title != group_item[2]:
                self.group_model.update_group(group.id, group.username, group.title,
                                                  group.participants_count, today_date)
                logger.info(f"Update group {group.id},{group.username},{group.title}")

            # 因Telegram API限制，无法获取全部群组成员；"aggressive" Does nothing
            # TODO: 需要记录获取成员失败的群，后续二次处理
            try:
                members = self.client.get_participants(id, aggressive=True)
            except Exception as e:
                logger.error(f"Failed to get participants of group {id},{username},{title}: {e}")
                continue

            for member in members:
                # 过滤bot、广告号、已经爬过的用户，减少TG请求
                # TODO: 可能用户信息会更新，需要重新爬取
                if member.bot:
                    continue
                if filter_entity_by_title(member.first_name) or filter_entity_by_title(member.last_name):
                    logger.info(f"Filter member {member.first_name},{member.last_name} for group {id},{username},{title}")
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
                    logger.info(f"Add new user {member.id},{member.username} to db")
                if not self.group_model.is_user_in_group(id, member.id):
                    self.group_model.add_user_to_group(id, member.id, today_date)
                    logger.info(f"Add new user {member.id},{member.username} to group {id},{username},{title}")

                # 根据 about 再次过滤广告号，广告号没有价值且处理麻烦
                if filter_entity_by_info(about):
                    continue

                # 从info中获取新的群组或频道
                chat_names = find_channel(about)
                if len(chat_names) < 1:
                    continue

                group_city = group_item[4]
                member_text = (member.first_name if member.first_name else "") + " " \
                                + (member.last_name if member.last_name else "") + " " + about
                member_city = self.group_agent.get_city_from_text(member_text, threshold=1)
                if member_city == None:
                    member_city = group_city
                self.process_chat_names(chat_names, member_city)

    # 获取群组消息，从群组消息中获取group或channel
    def get_group_messages(self) -> None:
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

    def process_chat_names(self, chat_names: list, city: str) -> None:
        logger.info(f"Processing chat names {chat_names} from {city}")
        for chat_name in chat_names:
            if chat_name.lower().endswith("bot"):
                continue
            if chat_name in processed_chat_names:
                logger.info(f"Already checked chat: {chat_name}")
                continue
            else:
                processed_chat_names[chat_name] = 1

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

            # 过滤 User
            if isinstance(chat, User):
                logger.info(f"Ignore chat as user: {chat_name}")
                continue
            # 如果是 Group
            if chat.megagroup == True:
                self.group_agent.process_group(chat)
            # 如果是 Channel
            else:
                self.process_channel(chat, city)

    def process_channel(self, channel: Channel, city: str):
        logger.info(f"Processing channel: {channel.id},{channel.username},{channel.title}")
        # 过滤广告、已经抓取过的Channel
        if filter_entity_by_title(channel.title):
            logger.info(f"Filter ad channel: {channel.id},{channel.username},{channel.title}")
            return

        if self.channel_model.does_channel_exist(channel.id):
            logger.info(f"Already added channel: {channel.id},{channel.username},{channel.title}")
            # channel的username和title可能会变化，需要更新
            channel_item = self.channel_model.get_channel_by_id(channel.id)
            if channel.username != channel_item[1] or channel.title != channel_item[2]:
                self.channel_model.update_channel(channel.id, channel.username, channel.title,
                                                  channel.participants_count, today_date)
                logger.info(f"Update channel {channel.id},{channel.username},{channel.title}")
            return
        
        self.channel_model.add_channel(channel.id, channel.username, channel.title,
                                       channel.participants_count, today_date)
        logger.info(f"Add new channel to db: {channel.id},{channel.username},{channel.title}")
        self.parse_channel(channel, city)

    # 抓取 channel 消息，并调用 LLM 判断 channel 类型
    def parse_channel(self, channel: Channel, city: str):
        pinned_messages, candidate_messages = self.channel_agent.get_channel_messages(channel)
        if pinned_messages == None and candidate_messages == None:
            logger.error(f"Get messages of channel {channel.id} error: {e}")
            return

        self.channel_model.increment_retries(channel.id)
        # 为了控制 prompt 的 token 数，优先用pinned消息，再用其他消息
        prompt_messages = []
        prompt_len = 0
        for message_text in pinned_messages:
            if prompt_len >= 3000:
                break
            prompt_messages.append(message_text)
            prompt_len += len(message_text)
        for message_text in candidate_messages:
            if prompt_len >= 3000:
                break
            # 太长的消息不加入prompt
            if len(message_text) > 1000:
                continue
            prompt_messages.append(message_text)
            prompt_len += len(message_text)

        prompt_content = ";".join(prompt_messages)
        if prompt_content == "":
            return

        # 调用 LLM 判断 channel 类型
        channel_type = self.channel_agent.llm_judge_type(prompt_content)
        logger.info(f"Channel {channel.id},{channel.username},{channel.title} is type {channel_type}")
        if channel_type != 0:
            self.channel_model.update_channel_type(channel.id, channel_type)

        # 对按摩师类型，继续调用 LLM
        if channel_type == 1:
            info_data = self.channel_agent.llm_get_info(city + channel.title, prompt_content)
            if info_data is None:
                return
            try:
                info = json.loads(info_data)
            except Exception as e:
                logger.error(f"Parse channel {channel.id},{channel.username},{channel.title} info error: {e}")
                return
            logger.info(f"Channel {channel.id},{channel.username},{channel.title} info {info}")

            if self.teacher_model.does_teacher_exist(channel.id):
                logger.info(f"Already added teacher: {channel.id},{channel.username}")
            else:
                name, city, district, age, price, height, weight, measurement, service = \
                    info.get("name"), info.get("city"), info.get("district"), info.get("age"), info.get("price"), \
                    info.get("height"), info.get("weight"), info.get("measurement"), info.get("service")
                self.teacher_model.add_teacher(channel.id, channel.username,
                                               name, city, district, age, price, height, weight, measurement, service,
                                               0, today_date)
                logger.info(f"Add new teacher to db: {channel.id},{channel.username}{name}")
        
        # 对导航类型，继续解析 channel 消息
        if channel_type == 2:
            all_chat_names = []
            for message_text in pinned_messages + candidate_messages:
                chat_names = find_channel(message_text)
                if len(chat_names) > 0:
                    all_chat_names.extend(chat_names)
            print(all_chat_names)
            all_chat_names = list(set(all_chat_names))
            print(all_chat_names)
