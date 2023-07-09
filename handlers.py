from telegram.ext import ContextTypes
from telegram import Update
from config import logger
from utils import (user_exists, add_user_to_db, send_init_mes, get_text_and_image, get_all_users,
                   remove_users_from_db, white_list, superuser_list, publish_post)


@white_list
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_init_mes(update, context)


@white_list
async def gathering_info(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if "other" in context.user_data:
        ans = await get_text_and_image(update, context)
        if ans:

            if ans.lower() == "да":
                published = await publish_post(update, context)
                if published:
                    await update.message.reply_text("Пост опубликован!")
                    username = update.effective_user.username
                    logger.info(f"Post was published by user {username}")
                else:
                    await update.message.reply_text("Пост не опубликован")
            else:
                await update.message.reply_text("Пост не опубликован")

        await send_init_mes(update, context)

    elif "sensors" in context.user_data:
        other = await get_text_and_image(update, context)
        if other:
            context.user_data["other"] = other
            if other == ".":
                context.user_data["other"] = None
            else:
                await update.message.reply_text(f"Дополнительная инф-ция - {other}")

            await update.message.reply_text("Публикуем пост?(Да/нет)")

    elif "allow_images" in context.user_data and not context.user_data["allow_images"]:
        sensors = await get_text_and_image(update, context)
        if sensors:
            context.user_data["sensors"] = sensors
            if sensors == ".":
                context.user_data["sensors"] = None
            else:
                await update.message.reply_text(f"Инф-ция о датчиках - {sensors}")

            await update.message.reply_text("Если осталось что-то еще, что нужно уточнить, то пропиши это сейчас.")

    elif "what_to_do" in context.user_data:
        context.user_data["allow_images"] = True
        repl = await get_text_and_image(update, context)
        if repl:
            context.user_data["allow_images"] = False
            await update.message.reply_text("Теперь пропишите все датчики, которые нужно завести, если таковые имеются")

    elif "client" in context.user_data:
        what_to_do = await get_text_and_image(update, context)
        if what_to_do:
            context.user_data["what_to_do"] = what_to_do
            if what_to_do == ".":
                context.user_data["what_to_do"] = None
            else:
                await update.message.reply_text(f"Тип обращения - {what_to_do}")

            await update.message.reply_text("Отправьте все необходимые изображения(фото ТС, заказ наряда, сим и пр.). "
                                            "Когда закончите, отправьте текстовое сообщение.")

    else:
        client = await get_text_and_image(update, context)
        if client:
            context.user_data["client"] = client
            if client == ".":
                context.user_data["client"] = None
            else:
                await update.message.reply_text(f"Название клиента - {client}")

            await update.message.reply_text('Напишите что нужно сделать("Заведите", "Замените", "Проверьте", '
                                            '"Замените сим", "Заблокируйте сим" и т.д.)')


@white_list
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    logger.info(f"Reset command by {update.effective_user.username}")
    await send_init_mes(update, context)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Ошибочка(, попробуй еще раз")
    logger.error(f"Error - {context.error}")
    await send_init_mes(update, context)


@superuser_list
async def add_users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    params = context.args
    logger.info(f"{update.effective_user.username} requests to add users {params} to white list")

    for username in params:

        if not user_exists(username):
            add_user_to_db(username)
            response = f"Пользователь '{username}' был добавлен в белый список бота."
            logger.info(f"{username} was added to white list")
        else:
            response = f"Пользователь '{username}' уже есть в белом листе."

        await context.bot.send_message(chat_id=update.message.chat_id, text=response)

    await send_init_mes(update, context)


@superuser_list
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    logger.info(f"{update.effective_user.username} requests to list users")
    users = get_all_users()

    if not users:
        response = "Нет пользователей."
    else:
        response = "Список пользователей:\n"
        for user in users:
            response += f"- @{user.username}\n"

    await context.bot.send_message(chat_id=update.message.chat_id, text=response)
    await send_init_mes(update, context)


@superuser_list
async def remove_users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    usernames = context.args
    logger.info(f"{update.effective_user.username} requests to delete {usernames} from white list")

    results = remove_users_from_db(usernames)

    response = "\n".join(results)

    if response:
        await context.bot.send_message(chat_id=update.message.chat_id, text=response)
        await send_init_mes(update, context)
