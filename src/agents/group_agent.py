from datetime import date
from configparser import ConfigParser
from loguru import logger
import jieba

from telethon.sync import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import Channel
from telethon.errors.rpcerrorlist import InviteRequestSentError, UserAlreadyParticipantError

from utils.chats import *
from models.group_model import GroupModel
from models.district_model import DistrictModel


today_date = date.today()
jieba.load_userdict('data/userdict.txt')

class GroupAgent():
    def __init__(self, client: TelegramClient, config: ConfigParser) -> None:
        self.client = client
        self.config = config

        # 群组的数据库模型
        self.db_host = config.get('DATABASE', 'db_host')
        self.db_user = config.get('DATABASE', 'db_user')
        self.db_password = config.get('DATABASE', 'db_password')
        self.db_database = config.get('DATABASE', 'db_database')
        self.group_model = GroupModel(host=self.db_host, user=self.db_user,
                                      password=self.db_password, database=self.db_database)
        self.district_model = DistrictModel(host=self.db_host, user=self.db_user,
                                          password=self.db_password, database=self.db_database)

        # 获取所有城市
        self.all_cities = {}
        for city in self.district_model.get_all_cities():
            city_id = city[0]
            city_name = city[1].rstrip("市")
            self.all_cities[city_name] = {}
            for district in self.district_model.get_districts_of_city(city_id):
                district_name = district[1]
                self.all_cities[city_name][district_name] = 0

    def get_city_from_text(self, text, threshold=3) -> str:
        district_counts = {}
        for city_name in self.all_cities.keys():
            district_counts[city_name] = 0

        tokens = [token for token in list(jieba.cut(text)) if token.strip() != ""]
        for token in tokens:
            for city_name in self.all_cities.keys():
                if token == city_name:
                    district_counts[city_name] += 1
                for district_name in self.all_cities[city_name]:
                    if token == district_name:
                        district_counts[city_name] += 1

        max_city = max(district_counts, key=district_counts.get)
        max_count = district_counts[max_city]
        if max_count >= threshold:
            return max_city
        return None

    def process_group(self, group: Channel):
        logger.info(f"Processing group {group.id},{group.username},{group.title}")
        # 过滤成员少于1000、广告、已经加入的Group
        # TODO: 判断是否是老师群
        if group.participants_count != None and group.participants_count < 1000:
            logger.info(f"Too few members in group {group.id},{group.username},{group.title}")
            return
        if filter_group_by_title(group.title):
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
            member_city = self.get_city_from_text(' ' . join([ name for name in member_names if name ]))
            if member_city:
                group_city = member_city
                logger.info(f"Group {group.id},{group.username},{group.title} in city {member_city} by members")

        # 如果根据群成员无法判断，就获取群消息来判断
        if group_city == None:
            try:
                messages = self.client.get_messages(group.id, limit=500)
            except Exception as e:
                logger.error(f"Failed to get messages of group {group.id},{group.username},{group.title}: {e}")
            else:
                messages_text = ' ' . join([ message.message.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ') 
                                 for message in messages if message.message ])
                message_city = self.get_city_from_text(messages_text)
                if message_city:
                    group_city = message_city
                    logger.info(f"Group {group.id},{group.username},{group.title} in city {message_city} by messages")

        # 如果根据群成员和群消息都无法判断，就直接根据群组名来判断（群组名可能不可信，所以最后才采用）
        if group_city == None:
            title_tokens = list(jieba.cut(group.title))
            for token in title_tokens:
                for city_name in self.all_cities.keys():
                    if token == city_name:
                        group_city = city_name
            logger.info(f"Group {group.id},{group.username},{group.title} in city {group_city} by title")

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
