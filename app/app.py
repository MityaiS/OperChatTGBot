from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import token, logger
from handlers import start, gathering_info, error_handler, reset, add_users, list_users, remove_users


if __name__ == '__main__':

    application = Application.builder().token(token).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    gathering_info_handler = MessageHandler((filters.TEXT | filters.PHOTO) & (~filters.COMMAND), gathering_info)
    application.add_handler(gathering_info_handler)

    reset_handler = CommandHandler("reset", reset)
    application.add_handler(reset_handler)

    add_users_handler = CommandHandler("add_users", add_users)
    application.add_handler(add_users_handler)

    list_users_handler = CommandHandler("list_users", list_users)
    application.add_handler(list_users_handler)

    remove_users_handler = CommandHandler("remove_users", remove_users)
    application.add_handler(remove_users_handler)

    application.add_error_handler(error_handler)

    logger.debug("polling...")
    application.run_polling()
