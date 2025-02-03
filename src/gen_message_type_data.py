import json
from http import HTTPStatus
from loguru import logger

import dashscope
from utils.chats import *

logger.add(
    "kt.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss}\t{level}\t{name}\t{message}",
    encoding="utf-8"
)

def main() -> None:
    feedback_prompt_template_file = 'config/feedback_prompt_template.txt'
    try:
        feedback_prompt_template = read_prompt_template(feedback_prompt_template_file)
    except FileNotFoundError as e:
        logger.error(f"Prompt template file not found: {feedback_prompt_template_file}")
        return

    f = open("channel_messages.csv")
    for line in f:
        columns = line.strip().split('\t')
        if len(columns) < 9:
            logger.error("Invalid line:", line)
            continue
        message = columns[2]
        # 读取prompt模板文件
        system_prompt = feedback_prompt_template % (message)
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
            logger.error(f"LLM parse feedback error for {message}: {e}")
            continue

        if response.status_code != HTTPStatus.OK:
            logger.error(f"LLM parse feedback wrong code for {message}: {response}")
            continue
        feedback_data = clean_json_string(response.output.choices[0].message.content)
        if feedback_data is None or not feedback_data:
            logger.error(f"LLM response empty for {message}")
            continue
        try:
            feedback = json.loads(feedback_data)
            feedback_type = feedback.get("type")
            print(f"{message}\t{feedback_type}")
        except Exception as e:
            logger.error(f"LLM feedback response error for {message}: {e}")
            continue

if __name__ == "__main__":
    main()
