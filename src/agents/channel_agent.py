import os
import logging
import csv
from datetime import date
from configparser import ConfigParser

from telethon.sync import TelegramClient
from telethon.tl.types import Channel, MessageMediaPhoto

from paddleocr import PaddleOCR
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

        prompt_template_file = 'config/prompt_template.txt'
        try:
            self.prompt_template = read_prompt_template(prompt_template_file)
        except FileNotFoundError as e:
            logger.error(f"Prompt template file not found: {prompt_template_file}")

    def llm_parse(self, content: str):
        # 读取prompt模板文件
        system_prompt = self.prompt_template % (content)
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
            return None
        return response

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

                    photo_text_list = []
                    for ocr_result in ocr_results:
                        if ocr_result == None:
                            break
                        for text in ocr_result:
                            photo_text_list.append(text[-1][0])
                    if len(photo_text_list) > 0:
                        photo_text = ' '.join(photo_text_list)
                        message_text = photo_text + ' ' + message_text
                pinned_messages.append(message_text)
            else:
                candidate_messages.append(message_text)
            
            self.channel_model.add_message_to_channel(channel.id, message.id, message_text, message.pinned,
                                                      comments, replies, reactions, views, message.date)

        prompt_messages = []
        content_len = 0
        for message_text in pinned_messages:
            if content_len >= 5000:
                break
            prompt_messages.append(message_text)
            content_len += len(message_text)
        for message_text in candidate_messages:
            if content_len >= 5000:
                break
            prompt_messages.append(message_text)
            content_len += len(message_text)

        content = ";".join(prompt_messages)
        if content == "":
            return

        response = self.llm_parse(content)
        if response == None:
            logger.error(f"LLM parse error for channel {channel.id}")
            return

        print(content)
        print(response)

    def update_channels(self):
        all_channels = self.channel_model.get_all_channels()
        for channel in all_channels:
            print(f"=========================={channel[0]},{channel[1]},{channel[2]}")

            messages = self.channel_model.get_channel_messages(channel[0])

            # 为了控制prompt的token数，优先用pinned消息，再用其他消息
            pinned_messages, candidate_messages, prompt_messages = [], [], []
            for message in messages:
                message_text, pinned, comments, replies, reactions, views = message[2:8]
                if pinned:
                    pinned_messages.append(message_text)
                else:
                    candidate_messages.append(message_text)

            content_len = 0
            for message_text in pinned_messages:
                if content_len >= 5000:
                    break
                prompt_messages.append(message_text)
                content_len += len(message_text)
            for message_text in candidate_messages:
                if content_len >= 5000:
                    break
                prompt_messages.append(message_text)
                content_len += len(message_text)

            content = ";".join(prompt_messages)
            if content == "":
                continue

            # 读取prompt模板文件
            system_prompt = self.prompt_template % (content)
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
                print(f"LLM API error for {channel[0]}: {e}")
                continue
            print(content)
            print()
            print(response)
            print()

    def pp_channel_messages(self, channel_id):
        messages = self.channel_model.get_channel_messages(channel_id)

        # 为了控制prompt的token数，优先用pinned消息，再用其他消息
        pinned_messages, candidate_messages, prompt_messages = [], [], []
        for message in messages:
            message_text, pinned, comments, replies, reactions, views = message[2:8]
            if pinned:
                pinned_messages.append(message_text)
            else:
                candidate_messages.append(message_text)

        content_len = 0
        for message_text in pinned_messages:
            if content_len >= 5000:
                break
            prompt_messages.append(message_text)
            content_len += len(message_text)
        for message_text in candidate_messages:
            if content_len >= 5000:
                break
            prompt_messages.append(message_text)
            content_len += len(message_text)

        content = ";".join(prompt_messages)
        if content == "":
            return

        # 读取prompt模板文件
        system_prompt = self.prompt_template % (content)
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': ''}
            ]
        
        response = dashscope.Generation.call(
            api_key="sk-a7b8eb7981bf4b17b545a0caecfcaf50",
            model="qwen-plus",
            messages=messages,
            result_format='message',
            temperature=0.1
            )
        print(content)
        print()
        print(response)
