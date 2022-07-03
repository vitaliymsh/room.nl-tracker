import urllib.request, json
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

URL = 'https://studentenplatformapi.hexia.io/api/v1/actueel-aanbod?limit=5000&locale=en_GB&page=0&sort=-publicationDate'
TOKEN = '5521587588:AAEsc7WMcPYi-9ODu2yTos905oijXwccOQM'
OWNER_CHAT_ID = None
CHAT_IDS = []
TIME = 60
LISTINGS = set()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global OWNER_CHAT_ID
    if OWNER_CHAT_ID is None:
        OWNER_CHAT_ID = update.effective_chat.id
        CHAT_IDS.append(OWNER_CHAT_ID)
        await context.bot.send_message(chat_id=OWNER_CHAT_ID, text="Owner registered.")
    else:
        chat_id = update.effective_message.chat_id
        CHAT_IDS.append(chat_id)
        await context.bot.send_message(chat_id=chat_id, text="Registered as a user!")
        await context.bot.send_message(chat_id=OWNER_CHAT_ID, text="Someone else using the bot!")

async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    global LISTINGS
    job = context.job
    temp_data = []
    with urllib.request.urlopen(URL) as page:
        data = json.loads(page.read().decode())
        for item in data['data']:
            if item['city']['name'] == 'Delft' and int(item['publicationDate'][6]) >= 7:
                if not item['ID'] in LISTINGS:
                    LISTINGS.add(item['ID'])
                    temp_data.append([f"https://www.room.nl/en/offerings/to-rent/details/{item['urlKey']}", str(item['publicationDate'])])
    temp_data.sort(key=lambda x: x[1], reverse=True)
    if len(temp_data) != 0:
        for chat_id in CHAT_IDS:
            for i in range(3):
                await context.bot.send_message(chat_id, text="NEW LISTINGS FOUND!!!")
            for listing in temp_data:
                await context.bot.send_message(chat_id, text='\n'.join(listing))
    context.job_queue.run_once(alarm, TIME, chat_id=job.chat_id, name=str(job.chat_id), data=TIME)


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id
    # args[0] should contain the time for the timer in seconds
    due = TIME
    if due < 0:
        await update.effective_message.reply_text("Sorry we can not go back to future!")
        return

    job_removed = remove_job_if_exists(str(chat_id), context)
    context.job_queue.run_once(alarm, due, chat_id=chat_id, name=str(chat_id), data=due)

    text = "Timer successfully set!"
    if job_removed:
        text += " Old one was removed."
    await update.effective_message.reply_text(text)


async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    if chat_id == OWNER_CHAT_ID:
        job_removed = remove_job_if_exists(str(OWNER_CHAT_ID), context)
        text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    else:
        text = "You are not the owner"
    await update.message.reply_text(text)

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    application.add_handler(CommandHandler("set", set_timer))
    application.add_handler(CommandHandler("unset", unset))
    application.run_polling()


