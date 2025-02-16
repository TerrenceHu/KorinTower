from configparser import ConfigParser
from loguru import logger
import textwrap

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

logger.add(
    "student_bot.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss}\t{level}\t{name}\t{message}",
    encoding="utf-8"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    logger.info(f"User {user.first_name},{user.last_name},{user.username} started the conversation")

    keyboard = [
        [
            InlineKeyboardButton("我要出击", callback_data="1"),
            InlineKeyboardButton("提交报告", callback_data="2"),
            InlineKeyboardButton("打赏作者", callback_data="3"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    opening_line = f"""
    {user.first_name}{user.last_name} 您好，我是好色的龟仙人！

    👙 我会什么 👙
    获取TG全网的「老师」资源，包括联系方式、反馈报告等，帮你发现心仪的「老师」！
    
    🔖 使用说明 🔖
    在下方选择您要的操作选项：
    1.「我要出击」：按位置、价格筛选，并查看报告，发现心仪的老师😍
    2.「提交报告」：出击后请及时提交报告，造福同学们🙏
    3.「打赏作者」：兄弟们，用根烟钱支持一下呗🤝

    更多功能敬请期待！使用反馈可联系 @roshicj
    ⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️
    """
    opening_line = textwrap.dedent(opening_line)

    await update.message.reply_text(opening_line, reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    await query.edit_message_text(text=f"Selected option: {query.data}")


def main() -> None:
    config = ConfigParser()
    config.read('config/bot_config.ini')
    token = config.get('TG_BOT', 'TOKEN')

    application = Application.builder().token(token).build()
    logger.info(f"Student bot start")

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
