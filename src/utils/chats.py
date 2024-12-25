import re

def find_channel(about):
    pattern = r't\.me/([\w+-]+)'
    matches = re.findall(pattern, str(about))
    
    return matches


# 过滤掉一些不需要的群
def filter_group_by_title(name: str) -> bool:    
    key_words = [u"赚", u"搞钱", u"日结", u"日搞", u"月入", u"红包", u"抽奖", u"彩金",
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
    key_words = [u"赚", u"搞钱", u"日结", u"日搞", u"月入", u"红包", u"抽奖", u"彩金", 
                 u"交易", u"客服", u"代理", u"推广", u"招商", u"平台", u"主营", u"安排",
                 u"广告", u"软件", u"接码", u"老店", u"机器人", u"号商", u"项目", u"公群",
                 u"进群", u"进裙", u"会所", u"水汇", u"商K", u"KTV", u"体验馆", u"情趣用品"]
    for key_word in key_words:
        if key_word in str(name):
            return True
    return False

# 过滤掉一些非老师的群成员
def filter_entity_by_info(info: str) -> bool:
    key_words = [u"赚", u"搞钱", u"日结", u"日搞", u"月入", u"红包", u"抽奖", u"彩金", 
                 u"交易", u"客服", u"代理", u"推广", u"招商", u"平台", u"主营", u"安排",
                 u"全国", u"广告", u"软件", u"接码", u"老店", u"公群"]
    for key_word in key_words:
        if key_word in str(info):
            return True
    return False