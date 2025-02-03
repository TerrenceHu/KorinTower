import os, re

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
    return None

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

def remove_nsfw_keywords(text: str) -> str:
    """从文本中删除指定的关键词"""
    keywords = [u"奶子", u"小穴", u"肉穴", u"蜜穴", u"乳头", u"肉棒", u"调教", u"耳光", u"鞭打", u"勾引",
                u"体位", u"后入", u"女上位", u"69", u"戴套", u"屌感", u"全裸", u"波推", u"漫游", u"丝足",
                u"口活", u"口交", u"口爆", u"无T口", u"足交", u"深喉", u"舌吻", u"蛇吻", u"Sm", u"SM",
                u"啪啪", u"爱爱", u"做爱", u"抽插", u"艹", u"陪洗", u"鸳鸯浴", u"吹箫", u"毒龙", u"双飞",
                u"潮吹", u"潮喷", u"强奸"]
    # 使用正则表达式匹配关键词，并替换为空字符串
    pattern = re.compile(r'(' + '|'.join(re.escape(keyword) for keyword in keywords) + r')')
    cleaned_text = pattern.sub('', text)
    return cleaned_text