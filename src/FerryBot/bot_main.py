import datetime
import logging
import os

import pandas as pd
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ApplicationBuilder

from FerryBot.fetch_bus_location import fetch_main

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

JOB_NAME_REPEAT = "run_bus_repeat"
JOB_NAME_ONCE = "run_bus_once"
POLL_INTERVAL = 15 # every 15 seconds

def bus_notify_filter(bus: dict) -> bool:
    return bus["st"] in {49,50} and bus["direction"] == "WEST" and bus["range_left"] <= 7  ## bus between 5 and 7


def time_of_day_filter() -> bool:
    return datetime.time(17, 10) <= pd.Timestamp.now().time() <= datetime.time(18, 30)


async def get_bus_once(context: ContextTypes.DEFAULT_TYPE):
    bus_notifications = await fetch_main(apply_filter=True, bus_notify_filter=bus_notify_filter)
    msg = ";".join(bus_notifications)
    await context.bot.send_message(chat_id=context.job.chat_id, text=msg if msg else "no bus on 49 toward west")


async def get_bus_repeat(context: ContextTypes.DEFAULT_TYPE):
    if not time_of_day_filter():
        return

    bus_notifications = await fetch_main(apply_filter=True, bus_notify_filter=bus_notify_filter)
    if bus_notifications:
        await context.bot.send_message(chat_id=context.job.chat_id, text=";".join(bus_notifications))


async def job_setup_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="...start polling")
    if context.job_queue.get_jobs_by_name(JOB_NAME_REPEAT):
        context.job_queue.get_jobs_by_name(JOB_NAME_REPEAT)[0].enabled = True
    else:
        context.job_queue.run_repeating(get_bus_repeat, interval=POLL_INTERVAL, name=("%s" % JOB_NAME_REPEAT), chat_id=chat_id)


async def job_run_once(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="...fetching")
    context.job_queue.run_once(get_bus_once, when=0, name=JOB_NAME_ONCE, chat_id=chat_id)  # now


async def job_disable_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="pause polling")
    context.job_queue.get_jobs_by_name(JOB_NAME_REPEAT)[0].enabled = False


if __name__ == "__main__":
    token_file = os.path.join(os.path.dirname(__file__), "../../../ferry_bot.token")
    with open(token_file, "r") as token:
        FerryByHipoBot_Token = token.readline()[:-1]
    application = ApplicationBuilder().token(FerryByHipoBot_Token).build()
    job_queue = application.job_queue
    application.add_handler(CommandHandler("start", job_setup_repeat))
    application.add_handler(CommandHandler("stop", job_disable_repeat))
    application.add_handler(CommandHandler("once", job_run_once))
    application.run_polling()
