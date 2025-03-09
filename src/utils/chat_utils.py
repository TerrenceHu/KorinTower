import os, re
from configparser import ConfigParser
from loguru import logger
from collections import Counter
import jieba

from telethon.sync import TelegramClient
from telethon.tl.types import User, Channel
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest

from globals import *
from models.district_model import DistrictModel

class ChatUtils:
    def __init__(self, client: TelegramClient, config: ConfigParser):
        self.client = client

        # district 的数据库模型
        self.db_host = config.get('DATABASE', 'db_host')
        self.db_user = config.get('DATABASE', 'db_user')
        self.db_password = config.get('DATABASE', 'db_password')
        self.db_database = config.get('DATABASE', 'db_database')
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

    # 根据文本判断城市
    def get_city_from_text(self, text, threshold) -> str:
        city_counts = {}
        for city_name in self.all_cities.keys():
            city_counts[city_name] = 0

        tokens = [token for token in list(jieba.cut(text)) if token.strip() != ""]
        for token in tokens:
            for city_name in self.all_cities.keys():
                if token == city_name:
                    city_counts[city_name] += 1
                for district_name in self.all_cities[city_name]:
                    if token == district_name:
                        city_counts[city_name] += 1

        max_city = max(city_counts, key=city_counts.get)
        max_count = city_counts[max_city]
        if max_count >= threshold:
            return max_city
        return None

    def get_user_about(self, user: User):
        try:
            full_member = self.client(GetFullUserRequest(user))
        except Exception as e:
            logger.error(f"Failed to GetFullUserRequest {user.id},{user.username}: {e}")
            return None

        about = full_member.full_user.about
        if about:
            about = about.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        return about

    def get_channel_about(self, channel: Channel):
        try:
            full_channel = self.client(GetFullChannelRequest(channel))
        except Exception as e:
            logger.error(f"Failed to GetFullChannelRequest {channel.id},{channel.username}: {e}")
            return None

        about = full_channel.full_chat.about
        if about:
            about = about.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        return about

    # 获取文本中 user、group 和 channel
    def get_chats_from(self, input_text: str):
        chat_names = self.find_usernames(input_text)
        if len(chat_names) < 1:
            return None, None, None

        logger.info(f"Processing chat names {chat_names}")
        user_chats, group_chats, channel_chats = [], [], []
        for chat_name in chat_names:
            if chat_name.lower().endswith("bot"):
                continue
            if chat_name in processed_usernames:
                logger.info(f"Already checked chat {chat_name}")
                continue
            processed_usernames[chat_name] = 1

            # TODO: private chat 怎么处理？
            if chat_name.startswith("+"):
                continue

            try:
                chat = self.client.get_entity(chat_name)
            except Exception as e:
                logger.error(f"Failed to get_entity {chat_name}: {e}")
                continue

            # 如果是 User
            if isinstance(chat, User):
                user_chats.append(chat)
            # 如果是 Group
            elif chat.megagroup == True:
                group_chats.append(chat)
            # 如果是 Channel
            else:
                channel_chats.append(chat)
        return user_chats, group_chats, channel_chats

    def get_user_from_text(self, channel: Channel, text: str) -> User:
        chat_names = self.find_usernames(text)
        logger.info(f"Fetch user from chat names {chat_names} in {text}")
        if len(chat_names) < 1:
            return None

        channel_user = None
        for chat_name in chat_names:
            if chat_name.lower().endswith("bot"):
                continue
            try:
                chat = self.client.get_entity(chat_name)
            except Exception as e:
                logger.error(f"Failed to get_entity {chat_name}: {e}")
                continue
            # 判断 channnel 是否能挂接到这个 user 上
            if isinstance(chat, User):
                user_about = self.get_user_about(chat)
                if self.filter_entity_by_about(user_about):
                    continue
                _, _, channel_chats = self.get_chats_from(user_about)
                if channel_chats:
                    for channel_chat in channel_chats:
                        if channel.username == channel_chat.username:
                            channel_user = chat
                            logger.info(f"Got user {chat.id},{chat.username} from channel {channel.id},{channel.username}")
                            return channel_user
        return None

    @staticmethod
    def find_usernames(input_text):
        pattern1 = r'@([\w_]+)'
        pattern2 = r't\.me/([\w+-]+)'

        matches1 = re.findall(pattern1, str(input_text))
        matches2 = re.findall(pattern2, str(input_text))
        matches = matches1 + matches2

        match_counts = Counter(matches)
        sorted_matches = sorted(match_counts.items(), key=lambda x: x[1], reverse=True)

        return [match[0] for match in sorted_matches]

    @staticmethod
    def clean_json_string(data: str) -> str:
        # 使用正则表达式匹配第一个 { 和最后一个 }
        data = data.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        match = re.search(r'\{.*?\}', data)
        if match:
            return match.group(0)
        return None

    # 过滤掉一些不需要的群
    @staticmethod
    def filter_group_by_title(name: str) -> bool:
        key_words = [u"赚", u"搞钱", u"日结", u"日搞", u"月入", u"红包", u"抽奖", u"彩金", u"博彩",
                     u"交易", u"客服", u"代理", u"推广", u"招商", u"平台", u"主营", u"安排",
                     u"广告", u"软件", u"接码", u"老店", u"机器人", u"号商", u"项目", u"公群",
                     u"进群", u"进裙", u"会所", u"水汇", u"商K", u"KTV", u"SPA", u"体验馆",
                     u"情趣用品", u"一条龙服务"]
        for key_word in key_words:
            if key_word in str(name):
                return True
        return False

    # 过滤掉一些非老师的群成员
    @staticmethod
    def filter_entity_by_title(name: str) -> bool:
        key_words = [u"赚", u"搞钱", u"日结", u"日搞", u"月入", u"红包", u"抽奖", u"彩金", u"博彩",
                     u"交易", u"客服", u"代理", u"推广", u"招商", u"平台", u"主营", u"安排",
                     u"广告", u"软件", u"接码", u"老店", u"机器人", u"号商", u"项目", u"公群",
                     u"进群", u"进裙", u"会所", u"水汇", u"商K", u"KTV", u"体验馆", u"情趣用品"]
        for key_word in key_words:
            if key_word in str(name):
                return True
        return False

    # 过滤掉一些非老师的群成员
    @staticmethod
    def filter_entity_by_about(info: str) -> bool:
        key_words = [u"赚", u"搞钱", u"日结", u"日搞", u"月入", u"红包", u"抽奖", u"彩金", u"博彩",
                     u"交易", u"客服", u"代理", u"招商", u"平台", u"主营", u"安排",
                     u"全国", u"广告", u"软件", u"接码", u"老店", u"公群"]
        for key_word in key_words:
            if key_word in str(info):
                return True
        return False

    @staticmethod
    def read_prompt_template(file_path: str) -> str:
        """读取prompt模板文件"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Prompt template file not found: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    @staticmethod
    def remove_nsfw_keywords(text: str) -> str:
        """从文本中删除指定的关键词"""
        keywords = [u"奶子", u"小穴", u"肉穴", u"蜜穴", u"乳头", u"肉棒", u"龟头", u"调教", u"耳光", u"鞭打",
                    u"体位", u"后入", u"女上位", u"69", u"戴套", u"带套", u"屌感", u"吊感", u"波推", u"漫游",
                    u"口活", u"口交", u"口爆", u"无T口", u"足交", u"深喉", u"舌吻", u"蛇吻", u"Sm", u"SM",
                    u"丝足", u"啪啪", u"爱爱", u"做爱", u"抽插", u"艹", u"陪洗", u"鸳鸯浴", u"吹箫", u"毒龙",
                    u"双飞", u"胸推", u"臀推", u"无套", u"三点粉", u"三点", u"水中萧", u"水萧", u"马眼", u"口技",
                    u"勾引", u"全裸", u"私处", u"骚话", u"潮吹", u"潮喷", u"强奸", u"高潮", u"颜射", u"乳交",
                    u"蛋蛋", u"白虎", u"女上", u"骑乘", u"叫床"]
        # 使用正则表达式匹配关键词，并替换为空字符串
        pattern = re.compile(r'(' + '|'.join(re.escape(keyword) for keyword in keywords) + r')')
        cleaned_text = pattern.sub('', text)
        return cleaned_text
