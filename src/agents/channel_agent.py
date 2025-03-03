import os
import json
from datetime import date
from http import HTTPStatus
from configparser import ConfigParser
from loguru import logger
import paddleocr
import dashscope

from telethon.sync import TelegramClient
from telethon.tl.types import User, Channel, MessageMediaPhoto

from utils.chat_utils import ChatUtils
from models.channel_model import ChannelModel
from models.teacher_model import TeacherModel
from models.district_model import DistrictModel

today_date = date.today()

class ChannelAgent():
    def __init__(self, client: TelegramClient, config: ConfigParser) -> None:
        self.client = client

        self.db_host = config.get('DATABASE', 'db_host')
        self.db_user = config.get('DATABASE', 'db_user')
        self.db_password = config.get('DATABASE', 'db_password')
        self.db_database = config.get('DATABASE', 'db_database')
        self.channel_model = ChannelModel(host=self.db_host, user=self.db_user,
                                          password=self.db_password, database=self.db_database)
        self.teacher_model = TeacherModel(host=self.db_host, user=self.db_user,
                                          password=self.db_password, database=self.db_database)
        self.district_model = DistrictModel(host=self.db_host, user=self.db_user,
                                          password=self.db_password, database=self.db_database)
        
        # chat 相关的工具
        self.chat_utils = ChatUtils(client, config)
        # ocr 识别工具
        self.media_path = config.get('KT_APP', 'media_path')
        self.ocr = paddleocr.PaddleOCR(lang='ch', show_log=False)

        type_prompt_template_file = 'config/type_prompt_template.txt'
        try:
            self.type_prompt_template = self.chat_utils.read_prompt_template(type_prompt_template_file)
        except FileNotFoundError as e:
            logger.error(f"Prompt template file not found: {type_prompt_template_file}")

        info_prompt_template_file = 'config/info_prompt_template.txt'
        try:
            self.info_prompt_template = self.chat_utils.read_prompt_template(info_prompt_template_file)
        except FileNotFoundError as e:
            logger.error(f"Prompt template file not found: {info_prompt_template_file}")

    def fetch_channel_messages(self, channel: Channel, limit: int, reverse: bool = False):
        # 只抓取最早的200条消息进行存储，很可能包含老师的课表信息
        try:
            messages = self.client.get_messages(channel.id, limit=limit, reverse=reverse)
        except Exception as e:
            return None, None

        pinned_messages, class_messages, candidate_messages = [], [], []
        for message in messages:
            if not message.message and not message.pinned:
                continue
            # 消息是否可评论、回复数、点赞数、浏览数
            comments, replies, reactions, views = False, 0, 0, message.views
            if message.replies:
                comments = message.replies.comments
                replies = message.replies.replies
            if message.reactions:
                for result in message.reactions.results:
                    reactions += result.count

            # 只识别pinned消息中图片的文字信息
            message_text = message.message.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ') if message.message else ''
            if message.pinned:
                if isinstance(message.media, MessageMediaPhoto):
                    photo_text = self.parse_photo_text(message.media, channel.id, message.id)
                    if photo_text:
                        message_text = photo_text + ' ' + message_text
                pinned_messages.append(message_text)
            elif "课表" in message_text and len(message_text) < 100:
                # 有些非 pinned 的消息中包含课表图片，且文字一般不会太长
                if isinstance(message.media, MessageMediaPhoto):
                    photo_text = self.parse_photo_text(message.media, channel.id, message.id)
                    if photo_text:
                        message_text = photo_text + ' ' + message_text
                class_messages.append(message_text)
            else:
                candidate_messages.append(message_text)

            self.channel_model.add_message_to_channel(channel.id, message.id, message_text, message.pinned,
                                                      comments, replies, reactions, views, message.date)
        if len(class_messages) > 0:
            pinned_messages.extend(class_messages)

        return pinned_messages, candidate_messages

    # 为了控制 prompt 的 token 数，优先用pinned消息，再用其他消息
    def get_prompt_from_messages(self, pinned_messages, candidate_messages):
        prompt_messages = []
        prompt_len = 0
        for message_text in pinned_messages:
            prompt_messages.append(message_text)
            prompt_len += len(message_text)
            if prompt_len >= 3000:
                break
        for message_text in candidate_messages:
            # 太长的消息不加入prompt
            if len(message_text) > 1000:
                continue
            prompt_messages.append(message_text)
            prompt_len += len(message_text)
            if prompt_len >= 3000:
                break
        return ";" . join(prompt_messages)

    # 调用 LLM 判断 channel 类型：0-初始值，-1-失败，1-按摩师，2-导航，100-其他
    def llm_judge_channel_type(self, content: str) -> int:
        # 读取prompt模板文件
        system_prompt = self.type_prompt_template % (content)
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': ''}
            ]
        
        try:
            response = dashscope.Generation.call(
                api_key="sk-a7b8eb7981bf4b17b545a0caecfcaf50",
                model="qwen-plus",
                messages=messages,
                result_format='message',
                temperature=0.1
                )
            logger.info(f"{content}\t{response}")
        except Exception as e:
            logger.error(f"LLM parse type error for {content}: {e}")
            return -1
        
        if response.status_code != HTTPStatus.OK:
            logger.error(f"LLM parse type wrong code: {response}")
            system_prompt = self.type_prompt_template % (self.chat_utils.remove_nsfw_keywords(content))
            logger.info(self.chat_utils.remove_nsfw_keywords(content))
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': ''}
            ]
            try:
                response = dashscope.Generation.call(
                    api_key="sk-a7b8eb7981bf4b17b545a0caecfcaf50",
                    model="qwen-plus",
                    messages=messages,
                    result_format='message',
                    temperature=0.1
                )
            except Exception as e:
                logger.error(f"LLM parse type error again for {content}: {e}")
                return -1
            if response.status_code != HTTPStatus.OK:
                logger.error(f"LLM parse type wrong code again: {response}")
                return -1

        output = response.output.choices[0].message.content
        if output.startswith('按摩师'):
            return 1
        elif output.startswith('导航'):
            return 2
        elif output.startswith('其他'):
            return 100
        return 0

    # 调用 LLM 获取 channel 信息
    def llm_parse_teacher_info(self, channel: Channel, context_city: str, content: str):
        # 读取prompt模板文件
        title = context_city + channel.title
        system_prompt = self.info_prompt_template % (title, content)
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': ''}
            ]
        
        try:
            response = dashscope.Generation.call(
                api_key="sk-a7b8eb7981bf4b17b545a0caecfcaf50",
                model="qwen-plus",
                messages=messages,
                result_format='message',
                temperature=0.1
            )
        except Exception as e:
            logger.error(f"LLM parse info error for {channel.id},{channel.username},{channel.title}: {e}")
            return None
        
        if response.status_code != HTTPStatus.OK:
            logger.error(f"LLM parse info wrong code for {channel.id},{channel.username},{channel.title}: {response}")
            
            logger.info(content)
            safe_content = self.chat_utils.remove_nsfw_keywords(content)
            system_prompt = self.info_prompt_template % (title, safe_content)
            logger.info(safe_content)
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': ''}
            ]
            try:
                response = dashscope.Generation.call(
                    api_key="sk-a7b8eb7981bf4b17b545a0caecfcaf50",
                    model="qwen-plus",
                    messages=messages,
                    result_format='message',
                    temperature=0.1
                )
            except Exception as e:
                logger.error(f"LLM parse info error again for {channel.id},{channel.username},{channel.title}: {e}")
                return None
            if response.status_code != HTTPStatus.OK:
                logger.error(f"LLM parse info wrong code again for {channel.id},{channel.username},{channel.title}: {response}")
                return None

        info_data = response.output.choices[0].message.content
        info_data = self.chat_utils.clean_json_string(info_data)
        if info_data is None or not info_data:
            logger.error(f"LLM response empty for {channel.id},{channel.username},{channel.title}")
            return None
        
        try:
            info = json.loads(info_data)
        except Exception as e:
            logger.error(f"LLM response error for {channel.id},{channel.username},{channel.title}: {e}")
            return None
        return info

    def norm_and_add_teacher(self, channel: Channel, user_of_channel: User, teacher_info: dict):
        name, city, district, age, price, price1, height, weight, measurement, service = (
                        teacher_info.get("name"),
                        teacher_info.get("city"),
                        teacher_info.get("district"),
                        teacher_info.get("age"),
                        teacher_info.get("price"),
                        teacher_info.get("price1"),
                        teacher_info.get("height"),
                        teacher_info.get("weight"),
                        teacher_info.get("measurement"),
                        teacher_info.get("service")
                    )
        
        city_id = self.district_model.get_city_id_by_name(city)
        district_id = self.district_model.get_district_id_by_name(district, city_id)
        logger.info(f"{teacher_info},{city_id},{district_id}")
        
        self.teacher_model.add_teacher(channel.id, channel.username,
                                       user_of_channel.id, user_of_channel.username,
                                       name, city_id, district_id, price, price1,
                                       age, height, weight, measurement, service,
                                       today_date)
    def parse_photo_text(self, media_url, channel_id, message_id):
        file_name = os.path.join(self.media_path, f"{channel_id}_{message_id}.jpg")
        try:
            self.client.download_media(media_url, file_name)
            ocr_results = self.ocr.ocr(file_name, cls=False)
        except Exception as e:
            logger.error(f"Download or OCR error for {channel_id},{message_id}: {e}")
            return None

        photo_text_list = []
        for ocr_result in ocr_results:
            if ocr_result == None:
                break
            for line in ocr_result:
                photo_text_list.append(line[-1][0])

        photo_text = None
        if len(photo_text_list) > 0:
            photo_text = ' '.join(photo_text_list)
        return photo_text
