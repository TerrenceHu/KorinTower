import pytz
from datetime import date, datetime, timedelta
from configparser import ConfigParser
from loguru import logger

from telethon.sync import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import User, Channel, ChannelForbidden
from telethon.errors.rpcerrorlist import InviteRequestSentError, UserAlreadyParticipantError

from globals import *
from utils.chat_utils import ChatUtils

from agents.channel_agent import ChannelAgent
from models.group_model import GroupModel
from models.channel_model import ChannelModel
from models.user_model import UserModel
from models.teacher_model import TeacherModel
from algorithms.text_processor import TextProcessor

today_date = date.today()

class GroupAgent():
    def __init__(self, client: TelegramClient, config: ConfigParser) -> None:
        self.client = client
        self.channel_agent = ChannelAgent(client, config)

        # 群组、频道和用户的数据库模型
        self.db_host = config.get('DATABASE', 'db_host')
        self.db_user = config.get('DATABASE', 'db_user')
        self.db_password = config.get('DATABASE', 'db_password')
        self.db_database = config.get('DATABASE', 'db_database')
        self.group_model = GroupModel(host=self.db_host, user=self.db_user,
                                      password=self.db_password, database=self.db_database)
        self.channel_model = ChannelModel(host=self.db_host, user=self.db_user,
                                          password=self.db_password, database=self.db_database)
        self.user_model = UserModel(host=self.db_host, user=self.db_user,
                                    password=self.db_password, database=self.db_database)
        self.teacher_model = TeacherModel(host=self.db_host, user=self.db_user,
                                          password=self.db_password, database=self.db_database)
        # 消息分类器
        self.text_processor = TextProcessor(config)
        # chat 相关的工具
        self.chat_utils = ChatUtils(client, config)

        # 获取所有群组（数据库中纪录的、上次新加入的）、当前对话中的频道
        for dialog in client.get_dialogs():
            logger.info(f"Get dialog {dialog.name}")
            if dialog.is_group:
                self.process_group(dialog.entity)
            #elif dialog.is_channel:
            #    self.process_channel(dialog.entity, '')

    # 获取群组成员，从群组成员的 about 中获取新的 group 或 channel
    def get_group_members(self) -> None:
        for group_item in self.group_model.get_all_groups():
            # 过滤失效的 group
            if group_item[5] < 0:
                continue

            id, username, title = group_item[0:3]
            group_city = group_item[4]
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
            try:
                members = self.client.get_participants(id, aggressive=True)
            except Exception as e:
                logger.error(f"Failed to get participants of group {id},{username},{title}: {e}")
                continue

            for member in members:
                self.process_user(member, group_city)

    # 获取群组消息，从群组消息中获取 group 或 channel
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

    def process_user(self, user: User, context_city: str):
        # 过滤bot、广告号、已经爬过的用户，减少TG请求
        # TODO: 可能用户信息会更新，需要重新爬取
        if user.bot:
            return None
        if self.chat_utils.filter_entity_by_title(user.first_name) \
            or self.chat_utils.filter_entity_by_title(user.last_name):
            logger.info(f"Filter user {user.username}{user.first_name},{user.last_name}")
            return None
        if user.first_name == "" and user.last_name == "" and user.username == "":
            return None
        if self.user_model.does_user_exist(user.id):
            logger.info(f"Already added user {user.id},{user.username}")
            return None

        # 获取用户的 info，并根据 info 再次过滤广告号
        about = self.chat_utils.get_user_about(user)
        if self.chat_utils.filter_entity_by_info(about):
            return None

        self.user_model.add_user(user.id, user.username, user.first_name, user.last_name, about)
        logger.info(f"Add new user {user.id},{user.username} to db")

        # 如果从用户的 name 和 about 中获取到城市，则使用这个城市，否则就用群组的城市
        user_text = (user.first_name if user.first_name else "") + " " \
                        + (user.last_name if user.last_name else "") + " " + about
        user_city = self.chat_utils.get_city_from_text(user_text, threshold=1)
        if user_city == None:
            user_city = context_city

        user_chats, group_chats, channel_chats = self.chat_utils.get_chats_from(about)
        if group_chats:
            for group_chat in group_chats:
                self.process_group(group_chat)
        if channel_chats:
            for channel_chat in channel_chats:
                if not self.user_model.is_channel_on_user(user.id, channel_chat.id):
                    self.user_model.add_channel_on_user(user.id, channel_chat.id, today_date)
                    logger.info(f"Add channel {channel_chat.id} on {user.id}")
                self.process_channel(channel_chat, user_city, user)

    def process_channel(self, channel: Channel, context_city: str, user_of_channel: User = None):
        logger.info(f"Processing channel {channel.id},{channel.username},{channel.title} from {context_city}")
        # 过滤广告、已经抓取过的 channel
        if self.chat_utils.filter_entity_by_title(channel.title):
            logger.info(f"Filter ad channel {channel.id},{channel.username},{channel.title}")
            return None
        # 获取 channel 的 info，并根据 info 再次过滤广告号
        channel_about = self.chat_utils.get_channel_about(channel)
        if self.chat_utils.filter_entity_by_info(channel_about):
            return None

        if self.channel_model.does_channel_exist(channel.id):
            logger.info(f"Already added channel {channel.id},{channel.username},{channel.title}")
            # channel 的 username 和 title 可能会变化，需要更新
            channel_item = self.channel_model.get_channel_by_id(channel.id)
            if channel.username != channel_item[1] or channel.title != channel_item[2]:
                self.channel_model.update_channel(channel.id, channel.username, channel.title, today_date)
                logger.info(f"Update channel {channel.id},{channel.username},{channel.title}")
            # channel 类型：0-初始值，-1-失败，1-按摩师，2-导航，100-其他
            # 解析3次及以上仍然失败，就不再解析了
            if channel_item[5] <= 0 and channel_item[6] >= 3:
                return None
            # 如果是导航或其他，不再解析；如果是按摩师，且是一个 teacher，就不再解析了
            if channel_item[5] > 0:
                if channel_item[5] == 2 or channel_item[5] == 100:
                    return None
                if channel_item[5] == 1:
                    cur_teacher = self.teacher_model.get_teacher_by_channel_id(channel.id)
                    if cur_teacher:
                        return cur_teacher
        else:
            self.channel_model.add_channel(channel.id, channel.username, channel.title,
                                           channel.participants_count, channel_about, today_date)
            logger.info(f"Add new channel {channel.id},{channel.username},{channel.title} to db")

        # 抓取 channel 消息
        pinned_messages, candidate_messages = self.channel_agent.fetch_channel_messages(channel, limit=200, reverse=True)
        if pinned_messages == None and candidate_messages == None:
            logger.error(f"Empty messages of channel {channel.id}")
            return None
        prompt_content = self.channel_agent.get_prompt_from_messages(pinned_messages, candidate_messages)
        if prompt_content == "":
            return None

        self.channel_model.increment_retries(channel.id)
        # 调用 LLM 判断 channel 类型
        channel_type = self.channel_agent.llm_judge_channel_type(prompt_content)
        logger.info(f"Channel {channel.id},{channel.username},{channel.title} is type {channel_type}")
        if channel_type != 0:
            self.channel_model.update_channel_type(channel.id, channel_type)

        # 对按摩师类型，继续调用 LLM
        if channel_type == 1:
            # 优先用新的 channel 消息
            prompt_content = self.channel_agent.get_prompt_from_messages(pinned_messages,
                                                                          candidate_messages[::-1])
            teacher_info = self.channel_agent.llm_parse_teacher_info(channel, context_city, prompt_content)
            if teacher_info:
                logger.info(f"Channel {channel.id},{channel.username},{channel.title} info {teacher_info}")
            else:
                logger.error(f"Failed to parse teacher info of channel {channel.id},{channel.username},{channel.title}")
                return None

            # 从 about 中获取 channel 归属的 user；若失败，再从 channel 内容中获取
            if user_of_channel == None:
                user_of_channel = self.chat_utils.get_user_from_text(channel, channel_about)
            if user_of_channel == None:
                user_of_channel = self.chat_utils.get_user_from_text(channel, prompt_content)
            if user_of_channel == None:
                logger.error(f"Failed to find user of channel {channel.id},{channel.username},{channel.title}")
                return None

            if not self.user_model.is_channel_on_user(user_of_channel.id, channel.id):
                self.user_model.add_channel_on_user(user_of_channel.id, channel.id, today_date)
                logger.info(f"Add channel {channel.id},{channel.username} on user {user_of_channel.id},{user_of_channel.username}")

            if teacher_info:
                if self.teacher_model.does_teacher_exist(channel.id):
                    logger.info(f"Already added teacher {channel.id},{channel.username},{user_of_channel.id},{user_of_channel.username}")
                else:
                    self.channel_agent.norm_and_add_teacher(channel, user_of_channel, teacher_info)
                    logger.info(f"Add new teacher {channel.id},{channel.username},{user_of_channel.id},{user_of_channel.username} to db")
                return self.teacher_model.get_teacher_by_channel_id(channel.id)

        # 对导航类型，继续解析 channel 消息
        elif channel_type == 2:
            pinned_messages, candidate_messages = self.channel_agent.fetch_channel_messages(channel, limit=1000)
            messages_text = ' ' . join(pinned_messages +  candidate_messages)
            channel_city = self.chat_utils.get_city_from_text(messages_text, threshold=3)
            if channel_city:
                context_city = channel_city
            for message_text in pinned_messages + candidate_messages:
                self.process_message(channel, context_city, message_text)
        return None

    def process_message(self, channel: Channel, context_city: str, message_text: str):
        logger.info(f"Processing message {message_text} from {channel.id},{channel.username},{context_city}")
        chat_names = self.chat_utils.find_chatnames(message_text)
        if len(chat_names) < 1:
            return
        logger.info(f"Process chat names {chat_names} from message")

        message_type = self.text_processor.predict(message_text)
        logger.info(f"Message {message_text} type {message_type}")

        for chat_name in chat_names:
            if chat_name.lower().endswith("bot"):
                continue
            if chat_name in processed_chat_names:
                logger.info(f"Already checked chat {chat_name}")
                continue
            processed_chat_names[chat_name] = 1
            if chat_name == channel.username:
                logger.info(f"Ignore self username {chat_name}")
                continue

            # TODO: private chat 怎么处理？
            if chat_name.startswith("+"):
                #self.join_private_chat(chat_name)
                continue

            try:
                chat = self.client.get_entity(chat_name)
            except Exception as e:
                logger.error(f"Failed to get_entity {chat_name}: {e}")
                continue

            # 如果是 User
            if isinstance(chat, User):
                logger.info(f"Chat {chat_name} is a user")
                self.process_user(chat, context_city)
            # 如果是 Group
            elif chat.megagroup == True:
                logger.info(f"Chat {chat_name} is a group")
                self.process_group(chat)
            # 如果是 Channel
            else:
                logger.info(f"Chat {chat_name} is a channel")
                result = self.process_channel(chat, context_city)

    def process_group(self, group: Channel):
        if isinstance(group, ChannelForbidden):
            logger.warning(f"Group {group.id} is forbidden")
            return
        
        logger.info(f"Processing group {group.id},{group.username},{group.title}")
        # 过滤成员少于1000、广告、已经加入的Group
        # TODO: 判断是否是老师群
        if group.participants_count != None and group.participants_count < 1000:
            logger.info(f"Too few members in group {group.id},{group.username},{group.title}")
            return
        if self.chat_utils.filter_group_by_title(group.title):
            logger.info(f"Filter ad group {group.id},{group.username},{group.title}")
            return
        if self.group_model.does_group_exist(group.id):
            logger.info(f"Already added group {group.id},{group.username},{group.title}")
            # group 的 username 和 title 可能会变化，需要更新
            group_item = self.group_model.get_group_by_id(group.id)
            if group.username != group_item[1] or group.title != group_item[2]:
                self.group_model.update_group(group.id, group.username, group.title,
                                                  group.participants_count, today_date)
                logger.info(f"Update group {group.id},{group.username},{group.title}")
            return
        
        self.group_model.add_group(group.id, group.username, group.title, group.participants_count, today_date)
        logger.info(f"Add new group {group.id},{group.username},{group.title} to db")

        group_city = None
        # 根据群成员的城市或辖区来判断群组归属的城市
        try:
            members = self.client.get_participants(group.id, aggressive=True)
        except Exception as e:
            logger.error(f"Failed to get participants of group {group.id},{group.username},{group.title}: {e}")
        else:
            member_names = []
            for member in members:
                member_names.append(member.first_name)
                member_names.append(member.last_name)
            member_names_text = ' ' . join([ name for name in member_names if name ])
            member_city = self.chat_utils.get_city_from_text(member_names_text, threshold=3)
            if member_city:
                group_city = member_city
                logger.info(f"Group {group.id},{group.username},{group.title} in city {member_city} from members")

        # 如果根据群成员无法判断，就获取群消息来判断
        if group_city == None:
            try:
                messages = self.client.get_messages(group.id, limit=500)
            except Exception as e:
                logger.error(f"Failed to get messages of group {group.id},{group.username},{group.title}: {e}")
            else:
                messages_text = ' ' . join([ message.message.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ') 
                                 for message in messages if message.message ])
                message_city = self.chat_utils.get_city_from_text(messages_text, threshold=3)
                if message_city:
                    group_city = message_city
                    logger.info(f"Group {group.id},{group.username},{group.title} in city {message_city} from messages")

        # 如果根据群成员和群消息都无法判断，就直接根据群组名来判断（群组名可能不可信，所以最后才采用）
        if group_city == None:
            title_city = self.chat_utils.get_city_from_text(group.title, threshold=1)
            if title_city:
                group_city = title_city
                logger.info(f"Group {group.id},{group.username},{group.title} in city {group_city} from title")

        if group_city:
            self.group_model.update_group_city(group.id, group_city)

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
