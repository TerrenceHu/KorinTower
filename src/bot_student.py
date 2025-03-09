from configparser import ConfigParser
from loguru import logger

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from bots.student_bot import StudentBot

logger.add(
    "logs/bot_student.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss}\t{level}\t{name}\t{message}",
    encoding="utf-8"
)

def main() -> None:
    config = ConfigParser()
    config.read('config/bot_config.ini')
    token = config.get('TG_BOT', 'TOKEN')

    application = Application.builder().token(token).build()
    logger.info(f"Student bot start")

    student_bot = StudentBot(config)

    application.add_handler(CommandHandler("start", student_bot.start))

    application.add_handler(CallbackQueryHandler(student_bot.handle_go, pattern="^go$"))
    application.add_handler(CallbackQueryHandler(student_bot.handle_city, pattern="^city"))
    application.add_handler(CallbackQueryHandler(student_bot.handle_district, pattern="^district"))
    application.add_handler(CallbackQueryHandler(
        student_bot.handle_pagination,
        pattern="^(prev_page|next_page)"
    ))

    application.add_handler(CallbackQueryHandler(student_bot.handle_feedback, pattern="^feedback$"))
    application.add_handler(CallbackQueryHandler(student_bot.handle_donate, pattern="^donate$"))
    

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
