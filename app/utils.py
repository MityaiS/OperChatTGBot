from enum import Enum
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config import Session, logger, target
import crud


class GatheringInfoStatus(Enum):
    CLIENT = 1
    WHAT_TO_DO = 2
    STATE_NUMBER_OR_VIN = 3
    ALLOW_IMAGES = 4
    WORK_ORDER = 5
    SENSORS = 6
    OTHER = 7


def white_list(func):

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, session: Session):
        username = update.effective_user.username

        if crud.user_exists(username, session):
            return await func(update, context, session)
        else:
            responce = """Ты не был добавлен в белый список. Попроси администратора, чтобы тебя добавили.
Как добавят, напиши /start"""
            await context.bot.send_message(chat_id=update.message.chat_id, text=responce)
            logger.info(f"Refused to user {update.effective_user.username}(not in white list)")
            await send_init_mes(update, context)

    return wrapper


def superuser_list(func):

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, session: Session):
        username = update.effective_user.username

        if crud.is_superuser(username, session):
            return await func(update, context, session)
        else:
            responce = "Вы не супер-пользоваталь. Мне очень жаль)"
            await context.bot.send_message(chat_id=update.message.chat_id, text=responce)
            logger.info(f"Refused to user {update.effective_user.username}(not Superuser)")
            await send_init_mes(update, context)

    return wrapper


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


async def send_init_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Через меня можно создать обращение в "
                                   "*оперативный чат*. Для этого отправь мне название клиента. Дальше я спрошу у "
                                   "тебя еще несколько вопросов и отправлю заявку в опер. чат. Чтобы начать "
                                   "составление заявки заново, оправь мне **/reset**. Если нужно пропустить поле, "
                                   "напиши '.'", parse_mode=ParseMode.MARKDOWN)

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Напиши название клиента...")
    context.user_data.clear()
    logger.info(f"Sent init message to {update.effective_user.username}")


async def get_text_and_image(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if GatheringInfoStatus.ALLOW_IMAGES.value in context.user_data \
            and context.user_data[GatheringInfoStatus.ALLOW_IMAGES.value]:

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


def escape_markdown(text):
    if not text:
        return None
    escaped_text = ""
    markdown_chars = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!']
    for char in text:
        if char in markdown_chars:
            escaped_text += '\\' + char
        else:
            escaped_text += char
    return escaped_text


async def publish_post(update: Update, context: ContextTypes.DEFAULT_TYPE, review: bool):

    post = ""

    client = escape_markdown(context.user_data[GatheringInfoStatus.CLIENT.value])
    what_to_do = escape_markdown(context.user_data[GatheringInfoStatus.WHAT_TO_DO.value])
    state_number_or_vin = escape_markdown(context.user_data[GatheringInfoStatus.STATE_NUMBER_OR_VIN.value])
    images = "images" in context.user_data
    sensors = escape_markdown(context.user_data[GatheringInfoStatus.SENSORS.value])
    other = escape_markdown(context.user_data[GatheringInfoStatus.OTHER.value])

    user = update.effective_user
    username = escape_markdown(user.username)
    first_name = escape_markdown(user.first_name)
    last_name = escape_markdown(user.last_name)
    full_name = f"{first_name} {last_name}" if last_name else first_name

    if what_to_do:
        post += f"*Что сделать*: {what_to_do}\n"

    if client:
        post += f"*Клиент*: {client}\n"

    if state_number_or_vin:
        post += f"*Гос. номер или VIN*: {state_number_or_vin}\n"

    if sensors:
        post += f"*Датчики*: {sensors}\n"

    if other:
        post += f"*Прочее*: {other}\n"

    if images:
        post += f"*Автор*: {full_name}(@{username})\n"
        logger.info(post)

        input_medias = []
        for image_id in context.user_data["images"]:
            input_media = InputMediaPhoto(media=image_id)
            input_medias.append(input_media)

        if review:
            await context.bot.send_media_group(chat_id=update.effective_chat.id, media=input_medias, caption=post,
                                               parse_mode=ParseMode.MARKDOWN)
        else:
            await context.bot.send_media_group(chat_id=target, media=input_medias, caption=post,
                                               parse_mode=ParseMode.MARKDOWN)

    elif post:
        post += f"*Автор*: {full_name}(@{username})\n"
        logger.info(post)

        if review:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=post, parse_mode=ParseMode.MARKDOWN)
        else:
            await context.bot.send_message(chat_id=target, text=post, parse_mode=ParseMode.MARKDOWN)

    else:
        return 0

    return 1
