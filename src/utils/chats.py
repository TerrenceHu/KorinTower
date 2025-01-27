import os
import re
import requests

def find_channel(about):
    pattern1 = r't\.me/([\w+-]+)'
    pattern2 = r'@([\w_]+)'
    
    matches1 = re.findall(pattern1, str(about))
    matches2 = re.findall(pattern2, str(about))
    matches = matches1 + matches2
    
    return matches

def clean_json_string(data: str) -> str:
    # 使用正则表达式匹配第一个 { 和最后一个 }
    data = data.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
    match = re.search(r'\{.*?\}', data)
    if match:
        return match.group(0)
    return data

# 过滤掉一些不需要的群
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
def filter_entity_by_info(info: str) -> bool:
    key_words = [u"赚", u"搞钱", u"日结", u"日搞", u"月入", u"红包", u"抽奖", u"彩金", u"博彩",
                 u"交易", u"客服", u"代理", u"推广", u"招商", u"平台", u"主营", u"安排",
                 u"全国", u"广告", u"软件", u"接码", u"老店", u"公群"]
    for key_word in key_words:
        if key_word in str(info):
            return True
    return False

def read_prompt_template(file_path: str) -> str:
    """读取prompt模板文件"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Prompt template file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
    
def call_qwen_plus(prompt: str, api_url: str, api_key: str) -> str:
    """调用通义千问Plus模型"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "prompt": prompt
    }
    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get("response", "")
    else:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
