import logging
import os

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ApplicationBuilder

from FerryBot.fetch_bus_location import fetch_main

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def bus_notify_filter(bus: dict) -> bool:
    return bus["st"] == 49 and bus["direction"] == "WEST" and 6 <= bus["range_left"] <= 7 ## bus between 5 and 7


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="start")


async def get_bus(context: ContextTypes.DEFAULT_TYPE):
    bus_notifications = await fetch_main(apply_filter=True, bus_notify_filter=bus_notify_filter)
    if bus_notifications:
        await context.bot.send_message(
            chat_id=context.job.chat_id, text=";".join(bus_notifications)
        )


async def set_bus_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="start polling")
    if context.job_queue.get_jobs_by_name("get_bus"):
        context.job_queue.get_jobs_by_name("get_bus")[0].enabled = True
    else:
        context.job_queue.run_repeating(get_bus, interval=5, name="get_bus", chat_id=chat_id)


async def disable_bus_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="pause polling")
    context.job_queue.get_jobs_by_name("get_bus")[0].enabled = False


if __name__ == "__main__":
    token_file = os.path.join(os.path.dirname(__file__), "../../../ferry_bot.token")
    with open(token_file, "r") as token:
        FerryByHipoBot_Token = token.readline()[:-1]
    application = ApplicationBuilder().token(FerryByHipoBot_Token).build()
    job_queue = application.job_queue
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("busstart", set_bus_job))
    application.add_handler(CommandHandler("stop", disable_bus_job))
    application.run_polling()
