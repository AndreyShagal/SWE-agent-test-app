from telegram import Bot, Update, ForceReply
from telegram.ext import  filters, Updater, CommandHandler, MessageHandler, CallbackContext
from langchain_community.callbacks import get_openai_callback
import yaml
import json
import tabulate
from datetime import datetime

import fin_analysis
import googlesheet


#load bot API params
with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

TG_key            = config['1320Lavanda_bot']['1320Lavanda_bot_api_key']
TG_chats          = config['1320Lavanda_bot']['1320Lavanda_bot_chats_ids']
TG_usernames_list = config['1320Lavanda_bot']['1320Lavanda_bot_ahpers_usernames']

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace these lists with the appropriate user IDs, usernames, and chat IDs
ALLOWED_USER_IDS = [ ]  # Example user IDs
ALLOWED_USERNAMES = TG_usernames_list  # Example usernames
ALLOWED_CHAT_IDS  = TG_chats  # Example chat IDs

async def is_user_allowed(user, chat_id):
    """
    Check if the user or chat is allowed to interact with the bot.

    :param user: The user object from the update.
    :param chat_id: The chat ID from the update.
    :return: True if the user is allowed, False otherwise.
    """
    username = user.username   #if user.username else user.first_name  - убираем, т.к. я могу создать акк. без юзернейма и назваться Имя = юзернейм и прорваться сквозь этот иф
    return (
        user.id in ALLOWED_USER_IDS or
        username in ALLOWED_USERNAMES or
        chat_id in ALLOWED_CHAT_IDS
    )



def format_table_from_json(json_data):
    """
    Format a table from the given JSON data using monospaced fonts for Telegram.
    """
    if isinstance(json_data, str):
        json_data = json.loads(json_data)  # Parse the JSON string into a Python dictionary

    # Extract the date and total profit
    date =   datetime.strptime(json_data["date"] , '%d-%m-%Y')
    total_profit = json_data["Total_profit"]

    # Extract the expenses information
    expenses = json_data["ExpensesList"]
    descriptions = json_data["ExpensesDescList"]
    types = json_data["ExpensesTypeList"]

    # Prepare the data for the table
    data = []
    for i in range(len(expenses)):
        data.append([
            #i + 1,   #убираем из таблицы нумерацию
            expenses[i],
            descriptions[i],
            #types[i]  #убераем тип затрат
        ])

    # Define headers
    headers = ["Затраты", "Описание"]
    # headers = ["#", "Expense (₽)", "Description" , "Type"]   - убрали нумерацию и тип затрат

    # Use the tabulate library to create a table
    table = tabulate.tabulate(data, headers, tablefmt="pipe")
    date_parsed  = date.strftime('%d %B %Y')
    # Combine the table with overall information
    summary = f"Дата: { date_parsed }\n"
    if total_profit != '' and  total_profit != 0:
        summary +=  f"Выручка: {total_profit}  \n\n"
    table_message = f"{summary}```\n{table}\n``` Получается так!"

    return table_message

async def send_table_message(update: Update, context: CallbackContext, json_data):
    # Format the table from the JSON data
    table_message = format_table_from_json(json_data)

    # Send the message with the table
    await update.message.reply_text(table_message, parse_mode='MarkdownV2')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")



async def handle_message(update: Update, context: CallbackContext):
    user = update.message.from_user
    # Checking if the user has a username, use it; otherwise use the first name
    username = user.username if user.username else user.first_name
    message_text = update.message.text
    chatname = update.effective_chat.effective_name
    chatid   = update.effective_chat.id

    if not await is_user_allowed(user, chatid):
        logger.warning(f'User {user.username} write to bot {message_text}')
        return -1

    #set reaction to message above
    # Attempt to add a 'like' reaction не работает в текущей версии
    if hasattr(context.bot, 'send_reaction'):
        # Newer versions of python-telegram-bot
        await context.bot.send_reaction(update.message.chat_id, update.message.message_id, '👍')


    logger.info(f"Message from {username}: {message_text}   :{chatname}:{chatid} ")
    with get_openai_callback() as cb:
        if fin_analysis.is_financial_report(message_text):
            await update.message.reply_text(f"Принято, @{username}-джан! Сейчас посчитаем...  \N{thumbs up sign}")
            financial_data = fin_analysis.parse_financial_data_to_JSON(message_text)
            logger.info(f"Financial Data: {financial_data}")

            await googlesheet.write_data_to_google_sheet(financial_data, username)

            await send_table_message(update, context, financial_data)
            #
        else:
            logger.info ("This is not a financial report.")

        logger.info (f"Total Tokens: {cb.total_tokens},  Prompt Tokens: {cb.prompt_tokens}, Completion Tokens: {cb.completion_tokens},Total Cost (USD): ${cb.total_cost}")


    return (username, message_text)

if __name__ == '__main__':
    application = ApplicationBuilder().token(TG_key).build()

    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message )

    application.add_handler(start_handler)
    application.add_handler(message_handler)

    application.run_polling()




