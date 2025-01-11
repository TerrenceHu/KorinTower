import os
import logging
from datetime import date
from configparser import ConfigParser

from telethon.sync import TelegramClient
from telethon.tl.types import Channel, MessageMediaPhoto

from paddleocr import PaddleOCR
from http import HTTPStatus
import dashscope

from models.channel_model import ChannelModel
from utils.chats import *


logger = logging.getLogger(__name__)
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

        self.media_path = config.get('APPLICATION', 'media_path')
        self.ocr = PaddleOCR(lang='ch')

        type_prompt_template_file = 'config/type_prompt_template.txt'
        try:
            self.type_prompt_template = read_prompt_template(type_prompt_template_file)
        except FileNotFoundError as e:
            logger.error(f"Prompt template file not found: {type_prompt_template_file}")

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
            print(content)
            print(response)
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

    # 抓取Channel消息，并调用LLM判断channel类型
    def parse_channel(self, channel: Channel):
        # 只抓取最早的200条消息进行存储，很可能包含老师的课表信息
        try:
            messages = self.client.get_messages(channel.id, limit=200, reverse=True)
        except Exception as e:
            logger.error(f"Get messages error for {channel.id}: {e}")
            return

        # 为了控制prompt的token数，优先用pinned消息，再用其他消息
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
        content_len = 0
        for message_text in pinned_messages:
            if content_len >= 3000:
                break
            prompt_messages.append(message_text)
            content_len += len(message_text)
        for message_text in candidate_messages:
            if content_len >= 3000:
                break
            # 太长的消息不加入prompt
            if len(message_text) > 1000:
                continue
            prompt_messages.append(message_text)
            content_len += len(message_text)

        content = ";".join(prompt_messages)
        if content == "":
            return

        channel_type = self.llm_judge_type(content)
        if channel_type != 0:
            self.channel_model.update_channel_type(channel.id, channel_type)
        
        if channel_type == 1:

        

    def batch_parse_channel(self):
        all_channels = self.channel_model.get_all_channels()
        for channel in all_channels:
            # 如果已经解析过，或者解析失败次数过多，跳过
            if channel[6] != 0 or channel[7] > 3:
                continue

            self.channel_model.increment_retries(channel[0])
            logger.info(f"parse channel: {channel[0]},{channel[1]},{channel[2]}")
            messages = self.channel_model.get_channel_messages(channel[0])

            # 为了控制prompt的token数，优先用pinned消息，再用其他消息
            pinned_messages, candidate_messages, prompt_messages = [], [], []
            for message in messages:
                message_text, pinned = message[2:4]
                if pinned:
                    pinned_messages.append(message_text)
                else:
                    candidate_messages.append(message_text)

            content_len = 0
            for message_text in pinned_messages:
                if content_len >= 3000:
                    break
                prompt_messages.append(message_text)
                content_len += len(message_text)
            for message_text in candidate_messages:
                if content_len >= 3000:
                    break
                # 太长的消息不加入prompt
                if len(message_text) > 1000:
                    continue
                prompt_messages.append(message_text)
                content_len += len(message_text)

            content = ";".join(prompt_messages)
            if content == "":
                continue

            channel_type = self.llm_judge_type(content)
            if channel_type != 0:
                self.channel_model.update_channel_type(channel[0], channel_type)

    def single_parse_channel(self, channel_id):
        self.channel_model.increment_retries(channel_id)
        try:
            channel = self.client.get_entity(channel_id)
        except Exception as e:
            logger.error(f"Failed to get_entity for channel {channel_id}: {e}")
            return
        
        logger.info(f"parse channel: {channel.id},{channel.username},{channel.title}")
        messages = self.channel_model.get_channel_messages(channel.id)

        # 为了控制prompt的token数，优先用pinned消息，再用其他消息
        pinned_messages, candidate_messages, prompt_messages = [], [], []
        for message in messages:
            message_text, pinned = message[2:4]
            if pinned:
                pinned_messages.append(message_text)
            else:
                candidate_messages.append(message_text)

        content_len = 0
        for message_text in pinned_messages:
            if content_len >= 3000:
                break
            prompt_messages.append(message_text)
            content_len += len(message_text)
        for message_text in candidate_messages:
            if content_len >= 3000:
                break
            # 太长的消息不加入prompt
            if len(message_text) > 1000:
                continue
            prompt_messages.append(message_text)
            content_len += len(message_text)

        content = ";".join(prompt_messages)
        if content == "":
            return
    
        channel_type = self.llm_judge_type(content)
        if channel_type != 0:
            self.channel_model.update_channel_type(channel.id, channel_type)

