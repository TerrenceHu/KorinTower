import os
from datetime import date
from configparser import ConfigParser
from loguru import logger
from http import HTTPStatus
import json
import paddleocr
import dashscope

from telethon.sync import TelegramClient
from telethon.tl.types import Channel, ChannelForbidden, MessageMediaPhoto

from models.channel_model import ChannelModel
from models.teacher_model import TeacherModel
from utils.chats import *


today_date = date.today()

logger.add(
    "kt.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss}\t{level}\t{name}\t{message}",
    encoding="utf-8"
)

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

        self.media_path = config.get('APPLICATION', 'media_path')
        self.ocr = paddleocr.PaddleOCR(lang='ch', show_log=False)

        type_prompt_template_file = 'config/type_prompt_template.txt'
        try:
            self.type_prompt_template = read_prompt_template(type_prompt_template_file)
        except FileNotFoundError as e:
            logger.error(f"Prompt template file not found: {type_prompt_template_file}")

        info_prompt_template_file = 'config/info_prompt_template.txt'
        try:
            self.info_prompt_template = read_prompt_template(info_prompt_template_file)
        except FileNotFoundError as e:
            logger.error(f"Prompt template file not found: {info_prompt_template_file}")

    # 抓取 channel 消息，并调用 LLM 判断 channel 类型
    def parse_channel(self, channel: Channel, city: str):
        # 只抓取最早的200条消息进行存储，很可能包含老师的课表信息
        try:
            messages = self.client.get_messages(channel.id, limit=200, reverse=True)
        except Exception as e:
            logger.error(f"Get messages of channel {channel.id} error: {e}")
            return

        # 为了控制 prompt 的 token 数，优先用pinned消息，再用其他消息
        pinned_messages, candidate_messages = [], []
        for message in messages:
            if not message.message:
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
            message_text = message.message.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
            if message.pinned:
                if isinstance(message.media, MessageMediaPhoto):
                    file_name = os.path.join(self.media_path, f"{channel.id}_{message.id}.jpg")
                    try:
                        self.client.download_media(message.media, file_name)
                        ocr_results = self.ocr.ocr(file_name, cls=False)
                    except Exception as e:
                        logger.error(f"Download or OCR error for {channel.id},{message.id}: {e}")
                    else:
                        photo_text_list = []
                        for ocr_result in ocr_results:
                            if ocr_result == None:
                                break
                            for line in ocr_result:
                                photo_text_list.append(line[-1][0])
                        if len(photo_text_list) > 0:
                            photo_text = ' '.join(photo_text_list)
                            message_text = photo_text + ' ' + message_text
                pinned_messages.append(message_text)
            else:
                candidate_messages.append(message_text)

            self.channel_model.add_message_to_channel(channel.id, message.id, message_text, message.pinned,
                                                      comments, replies, reactions, views, message.date)

        self.channel_model.increment_retries(channel.id)
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
        channel_type = self.llm_judge_type(prompt_content)
        logger.info(f"Channel {channel.id},{channel.username},{channel.title} is type {channel_type}")
        if channel_type != 0:
            self.channel_model.update_channel_type(channel.id, channel_type)

        # 对按摩师类型，继续调用 LLM
        if channel_type == 1:
            info_data = self.llm_get_info(city + channel.title, prompt_content)
            if info_data is None:
                return
            info_data = clean_json_string(info_data)
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

    def single_parse_channel(self, channel: Channel, channel_item: list):
        logger.info(f"Parse channel: {channel.id},{channel.username},{channel.title}")

        # 为了控制prompt的token数，优先用pinned消息，再用其他消息
        pinned_messages, candidate_messages, prompt_messages = [], [], []
        messages = self.channel_model.get_channel_messages(channel.id)
        for message in messages:
            message_text, pinned = message[2:4]
            if pinned:
                pinned_messages.append(message_text)
            else:
                candidate_messages.append(message_text)

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

        # 如果已经解析过 type，或者解析失败次数过多，跳过
        channel_type = channel_item[4]
        if channel_item[4] == 0 and channel_item[5] < 3:
            self.channel_model.increment_retries(channel.id)
            channel_type = self.llm_judge_type(prompt_content)
            if channel_type != 0:
                self.channel_model.update_channel_type(channel.id, channel_type)

        if channel_type == 1:
            self.llm_get_info(channel.title, prompt_content)

    def batch_parse_channel(self):
        all_channels = self.channel_model.get_all_channels()
        for channel_item in all_channels:
            # 过滤失效的channel
            if channel_item[6] < 1:
                continue
            # 先尝试用id获取channel，如果失败再尝试用username
            try:
                channel = self.client.get_entity(channel_item[0])
            except Exception as e:
                logger.error(f"Failed to get channel {channel_item[0]},{channel_item[1]},{channel_item[2]} by id: {e}")
                try:
                    if channel_item[1] is not None:
                        channel = self.client.get_entity(channel_item[1])
                        if isinstance(channel, ChannelForbidden):
                            logger.error(f"Channel {channel_item[0]},{channel_item[1]},{channel_item[2]} is forbidden")
                            raise(e)
                        if channel.id != channel_item[0]:
                            logger.error(f"Channel {channel_item[0]},{channel_item[1]},{channel_item[2]} is not the same as {channel.id}")
                            raise(e)
                    else:
                        raise(e)
                except Exception as e:
                    logger.error(f"Finally failed to get channel {channel_item[0]},{channel_item[1]},{channel_item[2]}: {e}")
                    self.channel_model.update_channel_status(channel_item[0], -1)
                    continue

            # channel的username和title可能会变化，需要更新
            if channel.username != channel_item[1] or channel.title != channel_item[2]:
                self.channel_model.update_channel(channel.id, channel.username, channel.title,
                                                  channel.participants_count, today_date)
                logger.info(f"Update channel {channel.id},{channel.username},{channel.title}")

            self.single_parse_channel(channel, channel_item)

    # 调用 LLM 判断 channel 类型：0-无法判断，1-按摩师，2-导航，100-其他
    def llm_judge_type(self, content: str) -> int:
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
            logger.info(content)
            logger.info(response)
        except Exception as e:
            logger.error(f"LLM parse type error for {content}: {e}")
            return 0
        if response.status_code != HTTPStatus.OK:
            logger.error(f"LLM parse type error {response}")
            return 0

        output = response.output.choices[0].message.content
        if output.startswith('按摩师'):
            return 1
        elif output.startswith('导航'):
            return 2
        elif output.startswith('其他'):
            return 100
        return 0

    # 调用 LLM 获取 channel 信息
    def llm_get_info(self, title: str, content: str):
        # 读取prompt模板文件
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
            logger.info(content)
            logger.info(response)
        except Exception as e:
            logger.error(f"LLM get info error for {content}: {e}")
            return None
        if response.status_code != HTTPStatus.OK:
            logger.error(f"LLM get info error {response}")
            return None

        return response.output.choices[0].message.content
