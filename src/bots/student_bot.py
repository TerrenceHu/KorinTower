from loguru import logger
from copy import deepcopy
from textwrap import dedent
from wcwidth import wcswidth

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from models.district_model import DistrictModel
from models.teacher_model import TeacherModel


def format_name_with_wcwidth(name, target_width, fillchar=' '):
    """使用 wcwidth 计算并格式化字符串"""
    current_width = wcswidth(name)
    padding_width = target_width - current_width
    if padding_width > 0:
        return name + fillchar * padding_width
    return name[:target_width]  # 如果超出目标宽度，截断


class StudentBot:
    def __init__(self, config):
        self.config = config

        # district 的数据库模型
        self.db_host = config.get('DATABASE', 'db_host')
        self.db_user = config.get('DATABASE', 'db_user')
        self.db_password = config.get('DATABASE', 'db_password')
        self.db_database = config.get('DATABASE', 'db_database')
        self.district_model = DistrictModel(host=self.db_host, user=self.db_user,
                                          password=self.db_password, database=self.db_database)
        self.teacher_model = TeacherModel(host=self.db_host, user=self.db_user,
                                          password=self.db_password, database=self.db_database)
        
        self.opening_line = dedent("""
        👙 <b>我会什么</b> 👙
        获取TG全网的「老师」资源，包括联系方式、反馈报告等，帮你发现心仪的「老师」！
        
        🔖 <b>使用说明</b> 🔖
        在下方选择您要的操作选项：
        1.「我要出击」：按位置、价格筛选，并查看报告，发现心仪的老师😍
        2.「提交报告」：出击后请及时提交报告，造福同学们🙏
        3.「打赏作者」：兄弟们，用根烟钱支持一下呗🤝

        更多功能敬请期待！使用反馈可联系 @roshihero
        ⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️
        """)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.message.from_user
        logger.info(f"User {user.id},{user.username} started the conversation")

        # 发送欢迎消息
        keyboard = [
            [
                InlineKeyboardButton("我要出击", callback_data="class"),
                InlineKeyboardButton("提交报告", callback_data="feedback"),
                InlineKeyboardButton("打赏作者", callback_data="donate"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        response = f"<b>{user.first_name}{user.last_name}</b> 您好，我是好色的龟仙人！\n{self.opening_line}"
        await update.message.reply_html(response, reply_markup=reply_markup)

    async def handle_class(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        effective_cities = self.district_model.get_effective_cities()
        keyboard, city_buttons, button_num = [], [], 0
        for city in effective_cities:
            city_id = city[0]
            city_name = city[1].rstrip("市")
            city_buttons.append(InlineKeyboardButton(city_name, callback_data=f"city_{city_id}_{city_name}"))
            button_num += 1
            if button_num % 5 == 0:
                keyboard.append(deepcopy(city_buttons))
                city_buttons = []
        else:
            if len(city_buttons) > 0:
                keyboard.append(deepcopy(city_buttons))
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        response = "请选择您所在的城市，目前支持以下城市："
        await query.message.reply_html(response, reply_markup=reply_markup)

    async def handle_city(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        city_id = query.data.split("_")[1] if "_" in query.data else None
        city_name = query.data.split("_")[2] if "_" in query.data else None
        if city_id is None:
            logger.error("Invalid city id in {query.data} for {user.id},{user.username}")
            return
        
        effective_teachers = self.teacher_model.get_effective_teachers_by_city(city_id)
        logger.info(f"{len(effective_teachers)} effective teachers in {city_id},{city_name}")
        # 一个城市的 teacher 太多，分区域检索
        if len(effective_teachers) > 100:
            keyboard, district_buttons, button_num = [], [], 0
            districts = self.district_model.get_districts_of_city(city_id)
            for district in districts:
                district_id = district[0]
                district_name = district[1].rstrip("区")
                district_buttons.append(InlineKeyboardButton(district[1], callback_data=f"district_{district_id}_{district_name}"))
                button_num += 1
                if button_num % 5 == 0:
                    keyboard.append(deepcopy(district_buttons))
                    district_buttons = []
            else:
                if len(district_buttons) > 0:
                    keyboard.append(deepcopy(district_buttons))
            reply_markup = InlineKeyboardMarkup(keyboard)
            response = f"请选择「{city_name}」的具体区域："
            await query.message.reply_html(response, reply_markup=reply_markup)
        else:
            response = f"<b>「{city_name}」</b>热门老师 ⬇️\n-------------------------\n"
            for teacher in effective_teachers[0:20]:
                user_username, name = teacher[3], teacher[4]
                deep_link = f"https://t.me/Fde123jilu/6"
                response += f"👱‍♀️ <b>{format_name_with_wcwidth(name, 12)}</b>私聊：@{user_username}\n"
                response += f"      <a href='{deep_link}'>报告1</a>\n"
            await query.message.reply_html(response, disable_web_page_preview=True)
    
    async def handle_district(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        district_id = query.data.split("_")[1] if "_" in query.data else None
        district_name = query.data.split("_")[2] if "_" in query.data else None
        if district_id is None:
            logger.error("Invalid district id in {query.data} for {user.id},{user.username}")
            return
        
        effective_teachers = self.teacher_model.get_effective_teachers_by_city(district_id)

    async def handle_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        response = "您选择了「提交报告」。请出击后请及时提交报告，造福同学们🙏"
        await query.message.reply_html(response)

    async def handle_donate(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        response = "您选择了「打赏作者」。兄弟们，用根烟钱支持一下呗🤝"
        await query.message.reply_html(response)