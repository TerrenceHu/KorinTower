import json
import dashscope
from utils.chats import *


def main() -> None:
    feedback_prompt_template_file = 'config/feedback_prompt_template.txt'
    try:
        feedback_prompt_template = read_prompt_template(feedback_prompt_template_file)
    except FileNotFoundError as e:
        print(f"Prompt template file not found: {feedback_prompt_template_file}")

    f = open("channel_messages.csv")
    for line in f:
        columns = line.strip().split('\t')
        if len(columns) < 9:
            print("Invalid line:", line)
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
            #print(message)
            #print(response)
        except Exception as e:
            print(f"LLM parse type error for {message}: {e}")

        try:
            feedback_data = clean_json_string(response.output.choices[0].message.content)
            feedback = json.loads(feedback_data)
            feedback_type = feedback.get("type")
            print(f"{message}\t{feedback_type}")
        except Exception as e:
            continue

if __name__ == "__main__":
    main()
