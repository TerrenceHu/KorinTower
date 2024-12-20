import re

def find_channel(about):
    pattern = r't\.me/([\w+-]+)'
    matches = re.findall(pattern, str(about))
    
    return matches


# 过滤掉一些非老师的群成员
def filter_ad_user(title: str) -> bool:
    key_words = [u"赚", u"搞钱", u"日结", u"会所", u"抽奖", u"机器人", u"进群", u"进裙",
                 u"项目", u"客服", u"代理", u"推广", u"招商", u"平台", u"彩金", u"主营",
                 u"交易", u"安排", u"全国", u"广告", u"软件", u"接码"]
    for key_word in key_words:
        if key_word in str(title):
            return True
    return False