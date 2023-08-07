from telegram.ext import ContextTypes
from telegram import Update
from config import logger, Session
import utils
import crud
from utils import GatheringInfoStatus


@utils.db_session
@utils.white_list
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, session: Session):
    await utils.send_init_mes(update, context)


@utils.db_session
@utils.white_list
async def gathering_info(update: Update, context: ContextTypes.DEFAULT_TYPE, session: Session):

    if GatheringInfoStatus.OTHER.value in context.user_data:
        ans = await utils.get_text_and_image(update, context)
        if ans:
            responce = "Пост не опубликован"
            if ans.lower() == "да":
                published = await utils.publish_post(update, context, review=False)
                if published:
                    responce = "Пост опубликован!"
                    username = update.effective_user.username
                    logger.info(f"Post was published by user {username}")

            await update.message.reply_text(responce)

        await utils.send_init_mes(update, context)

    elif GatheringInfoStatus.SENSORS.value in context.user_data:
        other = await utils.get_text_and_image(update, context)
        if other:
            context.user_data[GatheringInfoStatus.OTHER.value] = other
            if other == ".":
                context.user_data[GatheringInfoStatus.OTHER.value] = None
            else:
                await update.message.reply_text(f"Дополнительная инф-ция - {other}")

            await utils.publish_post(update, context, review=True)
            await update.message.reply_text("Публикуем пост?(Да/нет)")

    elif GatheringInfoStatus.ALLOW_IMAGES.value in context.user_data and \
            not context.user_data[GatheringInfoStatus.ALLOW_IMAGES.value]:
        sensors = await utils.get_text_and_image(update, context)
        if sensors:
            context.user_data[GatheringInfoStatus.SENSORS.value] = sensors
            if sensors == ".":
                context.user_data[GatheringInfoStatus.SENSORS.value] = None
            else:
                await update.message.reply_text(f"Инф-ция о датчиках - {sensors}")

            await update.message.reply_text("Если осталось что-то еще, что нужно уточнить, то пропиши это сейчас.")

    elif GatheringInfoStatus.ALLOW_IMAGES.value in context.user_data and GatheringInfoStatus.ALLOW_IMAGES.value \
            and GatheringInfoStatus.WORK_ORDER.value in context.user_data:
        ans = await utils.get_text_and_image(update, context)
        if ans:
            if ans.lower() == "да" or ans.lower() == "прикрепил":
                context.user_data[GatheringInfoStatus.ALLOW_IMAGES.value] = False
                responce = "Теперь пропиши все датчики, которые нужно завести, если таковые имеются"
            else:
                responce = "Надо прикрепить заказ-наряд... Как прикрепишь, отправь 'Прикрепил'"
            await update.message.reply_text(responce)

    elif GatheringInfoStatus.STATE_NUMBER_OR_VIN.value in context.user_data:
        context.user_data[GatheringInfoStatus.ALLOW_IMAGES.value] = True
        repl = await utils.get_text_and_image(update, context)
        if repl:
            context.user_data[GatheringInfoStatus.WORK_ORDER.value] = True
            await update.message.reply_text("Прикреплен ли заказ-наряд?(Да/нет)")

    elif GatheringInfoStatus.WHAT_TO_DO.value in context.user_data:
        state_number_or_vin = await utils.get_text_and_image(update, context)
        if state_number_or_vin:
            context.user_data[GatheringInfoStatus.STATE_NUMBER_OR_VIN.value] = state_number_or_vin
            if state_number_or_vin == ".":
                context.user_data[GatheringInfoStatus.STATE_NUMBER_OR_VIN.value] = None
            else:
                await update.message.reply_text(f"Гос. номер или VIN - {state_number_or_vin}")

            await update.message.reply_text("Отправь все необходимые изображения(фото ТС, заказ наряда, сим и пр.). "
                                            "Когда закончишь, отправь любое текстовое сообщение.")

    elif GatheringInfoStatus.CLIENT.value in context.user_data:
        what_to_do = await utils.get_text_and_image(update, context)
        if what_to_do:
            context.user_data[GatheringInfoStatus.WHAT_TO_DO.value] = what_to_do
            if what_to_do == ".":
                context.user_data[GatheringInfoStatus.WHAT_TO_DO.value] = None
            else:
                await update.message.reply_text(f"Тип обращения - {what_to_do}")

            await update.message.reply_text("Если действие связано с ТС, напиши гос. номер или VIN.")

    else:
        client = await utils.get_text_and_image(update, context)
        if client:
            context.user_data[GatheringInfoStatus.CLIENT.value] = client
            if client == ".":
                context.user_data[GatheringInfoStatus.CLIENT.value] = None
            else:
                await update.message.reply_text(f"Название клиента - {client}")

            await update.message.reply_text('Напиши что нужно сделать("Заведите", "Замените", "Проверьте", '
                                            '"Замените сим", "Заблокируйте сим" и т.д.)')


@utils.db_session
@utils.white_list
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE, session: Session):

    logger.info(f"Reset command by {update.effective_user.username}")
    await utils.send_init_mes(update, context)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    logger.error(f"Error - {context.error}")
    if update:
        await update.message.reply_text("Ошибочка(, попробуй еще раз")
        await utils.send_init_mes(update, context)


@utils.db_session
@utils.superuser_list
async def add_users(update: Update, context: ContextTypes.DEFAULT_TYPE, session: Session):

    params = context.args
    logger.info(f"{update.effective_user.username} requests to add users {params} to white list")

    for username in params:

        if not crud.user_exists(username, session):
            crud.add_user_to_db(username, session)
            response = f"Пользователь '{username}' был добавлен в белый список бота."
            logger.info(f"{username} was added to white list")
        else:
            response = f"Пользователь '{username}' уже есть в белом листе."

        await context.bot.send_message(chat_id=update.message.chat_id, text=response)

    await utils.send_init_mes(update, context)


@utils.db_session
@utils.superuser_list
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE, session: Session):

    logger.info(f"{update.effective_user.username} requests to list users")
    users = crud.get_all_users(session)

    if not users:
        response = "Нет пользователей."
    else:
        response = "Список пользователей:\n"
        for user in users:
            if user.superuser:
                response += f"- @{user.username} SU\n"
            else:
                response += f"- @{user.username}\n"

    await context.bot.send_message(chat_id=update.message.chat_id, text=response)
    await utils.send_init_mes(update, context)


@utils.db_session
@utils.superuser_list
async def remove_users(update: Update, context: ContextTypes.DEFAULT_TYPE, session: Session):

    usernames = context.args
    logger.info(f"{update.effective_user.username} requests to delete {usernames} from white list")

    results = crud.remove_users_from_db(usernames, session)

    response = "\n".join(results)

    if response:
        await context.bot.send_message(chat_id=update.message.chat_id, text=response)
        await utils.send_init_mes(update, context)
