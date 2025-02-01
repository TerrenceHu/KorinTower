import pytz
from datetime import date, datetime, timedelta
from configparser import ConfigParser
from loguru import logger

from telethon.sync import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import User, Channel, ChannelForbidden

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
            logger.info(f"Get dialog {dialog.name}")
            if dialog.is_group:
                self.group_agent.process_group(dialog.entity)

    # 获取群组成员，从群组成员的 about 中获取新的 group 或 channel
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
            try:
                members = self.client.get_participants(id, aggressive=True)
            except Exception as e:
                logger.error(f"Failed to get participants of group {id},{username},{title}: {e}")
                continue

            for member in members:
                chat_names = self.process_user(member)
                if not chat_names:
                    continue

                # 如果从用户的 name 和 about 中获取到城市，则使用这个城市，否则就用群组的城市
                member_text = (member.first_name if member.first_name else "") + " " \
                                + (member.last_name if member.last_name else "") + " " + about
                member_city = self.group_agent.get_city_from_text(member_text, threshold=1)
                group_city = group_item[4]
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

    def process_chat_names(self, chat_names: list, context_city: str) -> None:
        logger.info(f"Processing chat names {chat_names} from {context_city}")
        for chat_name in chat_names:
            if chat_name.lower().endswith("bot"):
                continue
            if chat_name in processed_chat_names:
                logger.info(f"Already checked chat {chat_name}")
                continue
            processed_chat_names[chat_name] = 1

            # TODO: 加入 private chat 怎么处理？
            if chat_name.startswith("+"):
                #self.join_private_chat(chat_name)
                continue

            try:
                chat = self.client.get_entity(chat_name)
            except Exception as e:
                logger.error(f"Failed to get_entity {chat_name}: {e}")
                continue

            # 过滤 User
            if isinstance(chat, User):
                logger.info(f"Ignore chat {chat_name} as user")
                continue
            # 如果是 Group
            if chat.megagroup == True:
                self.group_agent.process_group(chat)
            # 如果是 Channel
            else:
                self.process_channel(chat, context_city)

    def process_channel(self, channel: Channel, context_city: str):
        logger.info(f"Processing channel {channel.id},{channel.username},{channel.title} from {context_city}")
        # 过滤广告、已经抓取过的 channel
        if filter_entity_by_title(channel.title):
            logger.info(f"Filter ad channel {channel.id},{channel.username},{channel.title}")
            return None

        if self.channel_model.does_channel_exist(channel.id):
            logger.info(f"Already added channel {channel.id},{channel.username},{channel.title}")
            # channel 的 username 和 title 可能会变化，需要更新
            channel_item = self.channel_model.get_channel_by_id(channel.id)
            if channel.username != channel_item[1] or channel.title != channel_item[2]:
                self.channel_model.update_channel(channel.id, channel.username, channel.title,
                                                  channel.participants_count, today_date)
                logger.info(f"Update channel {channel.id},{channel.username},{channel.title}")
            # 解析3次及以上仍然失败，就不再解析了
            if channel_item[4] <= 0 and channel_item[5] >= 3:
                return None
            # TODO: 如果解析成功过，就不再解析了
            if channel_item[4] > 0:
                cur_teacher = self.teacher_model.get_teacher_by_id(channel.id)
                if cur_teacher:
                    return cur_teacher
                else:
                    return None
        else:
            self.channel_model.add_channel(channel.id, channel.username, channel.title,
                                       channel.participants_count, today_date)
            logger.info(f"Add new channel {channel.id},{channel.username},{channel.title} to db")

        # 抓取 channel 消息
        pinned_messages, candidate_messages = self.channel_agent.get_channel_messages(channel)
        #for message in pinned_messages:
        #    logger.info(f"---{message}")
        #for message in candidate_messages:
        #    logger.info(f"==={message}")
        if pinned_messages == None and candidate_messages == None:
            logger.error(f"Empty messages of channel {channel.id}")
            return None

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
            return None

        self.channel_model.increment_retries(channel.id)
        # 调用 LLM 判断 channel 类型
        channel_type = self.channel_agent.llm_judge_type(prompt_content)
        logger.info(f"Channel {channel.id},{channel.username},{channel.title} is type {channel_type}")
        if channel_type != 0:
            self.channel_model.update_channel_type(channel.id, channel_type)

        # 对按摩师类型，继续调用 LLM
        if channel_type == 1:
            return self.channel_agent.get_teacher_info(channel, context_city, prompt_content)
        # 对导航类型，继续解析 channel 消息
        elif channel_type == 2:
            for message_text in pinned_messages + candidate_messages:
                self.process_message(channel, context_city, message_text)
        return None

    def process_user(self, user: User):
        # 过滤bot、广告号、已经爬过的用户，减少TG请求
        # TODO: 可能用户信息会更新，需要重新爬取
        if user.bot:
            return None
        if filter_entity_by_title(user.first_name) or filter_entity_by_title(user.last_name):
            logger.info(f"Filter user {user.username}{user.first_name},{user.last_name}")
            return None
        if user.first_name == "" and user.last_name == "" and user.username == "":
            return None
        if self.user_model.does_user_exist(user.id):
            return None

        # 获取用户的info
        try:
            full_member = self.client(GetFullUserRequest(user))
        except Exception as e:
            logger.error(f"Failed to GetFullUserRequest {user.id},{user.username}: {e}")
            return None
        
        about = full_member.full_user.about
        if about:
            about = about.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        # 根据 about 再次过滤广告号，广告号没有价值且处理麻烦
        if filter_entity_by_info(about):
            return None

        if not self.user_model.does_user_exist(user.id):
            self.user_model.add_user(user.id, user.username, user.first_name, user.last_name, about)
            logger.info(f"Add new user {user.id},{user.username} to db")

        # 从info中获取新的群组或频道
        chat_names = find_channel(about)
        if len(chat_names) < 1:
            return None
        return chat_names

    def process_message(self, channel: Channel, context_city: str, message_text: str):
        chat_names = find_channel(message_text)
        if len(chat_names) < 1:
            return
        logger.info(f"Process message {chat_names}")  

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

            # TODO: 加入 private chat 怎么处理？
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
                chat_names = self.process_user(chat)
                logger.info(f"----111 {chat_names}")
                if not chat_names:
                    continue
                self.process_chat_names(chat_names, context_city)
            # 如果是 Group
            elif chat.megagroup == True:
                logger.info(f"----222 {chat_names}")
                self.group_agent.process_group(chat)
                logger.info(f"Get new group {chat_name} from {channel.id},{channel.username},{channel.title}")
            # 如果是 Channel
            else:
                logger.info(f"----333 {chat_names}")
                result = self.process_channel(chat, context_city)
                if result:
                    logger.info(f"Get new teacher {result} from {channel.id},{channel.username},{channel.title}")
        return
