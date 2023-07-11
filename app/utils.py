from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config import Session, logger
from models import User


def user_exists(username, session):
    existing_user = session.query(User).filter_by(username=username).first()
    return existing_user is not None


def add_user_to_db(username, session):
    user_db = User(username=username)
    session.add(user_db)
    session.commit()


async def send_init_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Через меня можно создать обращение в "
                                   "*оперативный чат*. Для этого отправь мне название клиента. Дальше я спрошу у "
                                   "тебя еще несколько вопросов и отправлю заявку в опер. чат. Чтобы начать "
                                   "составление заявки заново, оправь мне **/reset**. Если нужно пропустить поле, "
                                   "напиши '.'", parse_mode=ParseMode.MARKDOWN)

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Напиши название клиента...",
                                   parse_mode=ParseMode.MARKDOWN)
    context.user_data.clear()
    logger.info(f"Sent init message to {update.effective_user.username}")


async def get_text_and_image(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if "allow_images" in context.user_data and context.user_data["allow_images"]:

        try:
            file = update.message.photo[-1]
            file_id = file.file_id
        except:
            file = None
            file_id = None

        if file:
            if "images" not in context.user_data:
                context.user_data["images"] = [file_id]
            else:
                context.user_data["images"].append(file_id)

    text = update.message.text
    if text:
        return text.strip()
    return None


def get_all_users(session):
    return session.query(User).all()


def remove_users_from_db(usernames, session):

    results = []

    for username in usernames:
        user = session.query(User).filter_by(username=username).first()

        if user:
            session.delete(user)
            session.commit()
            results.append(f"Пользователь '{username}' был удален из белого листа.")
            logger.info(f"{username} was removed from white list")
        else:
            results.append(f"Пользователь '{username}' не был найден в белом листе.")

    return results


def white_list(func):

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, session: Session):
        username = update.effective_user.username

        if user_exists(username, session):
            return await func(update, context, session)
        else:
            text = """Ты не был добавлен в белый список. Попроси администратора, чтобы тебя добавили.
Как добавят, напиши /start"""
            await context.bot.send_message(chat_id=update.message.chat_id, text=text)
            logger.info(f"Refused to user {update.effective_user.username}(not in white list)")
            await send_init_mes(update, context)

    return wrapper


def is_superuser(username, session):
    user = session.query(User).filter_by(username=username).first()
    return user is not None and user.superuser


def superuser_list(func):

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, session: Session):
        username = update.effective_user.username

        if is_superuser(username, session):
            return await func(update, context, session)
        else:
            text = "Вы не супер-пользоваталь. Мне очень жаль)"
            await context.bot.send_message(chat_id=update.message.chat_id, text=text)
            logger.info(f"Refused to user {update.effective_user.username}(not Superuser)")
            await send_init_mes(update, context)

    return wrapper


async def publish_post(update: Update, context: ContextTypes.DEFAULT_TYPE, review: bool):

    post = ""

    client = context.user_data["client"]
    what_to_do = context.user_data["what_to_do"]
    images = "images" in context.user_data
    sensors = context.user_data["sensors"]
    other = context.user_data["other"]

    user = update.effective_user
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    full_name = f"{first_name} {last_name}" if last_name else first_name

    if what_to_do:
        post += f"*Что сделать*: {what_to_do}\n"

    if client:
        post += f"*Клиент*: {client}\n"

    if sensors:
        post += f"*Датчики*: {sensors}\n"

    if other:
        post += f"*Прочее*: {other}\n"

    if images:
        post += f"*Автор*: {full_name}(@{username})\n"

        input_medias = []
        for image_id in context.user_data["images"]:
            input_media = InputMediaPhoto(media=image_id)
            input_medias.append(input_media)

        if review:
            await context.bot.send_media_group(chat_id=update.effective_chat.id, media=input_medias, caption=post,
                                               parse_mode=ParseMode.MARKDOWN)
        else:
            await context.bot.send_media_group(chat_id="-1001592120085", media=input_medias, caption=post,
                                               parse_mode=ParseMode.MARKDOWN)

    elif post:
        post += f"*Автор*: {full_name}(@{username})\n"

        if review:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=post, parse_mode=ParseMode.MARKDOWN)
        else:
            await context.bot.send_message(chat_id="-1001592120085", text=post, parse_mode=ParseMode.MARKDOWN)

    else:
        return 0

    return 1


def db_session(bot_handler):

    def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()

        try:
            result = bot_handler(update, context, session)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    return wrapper
