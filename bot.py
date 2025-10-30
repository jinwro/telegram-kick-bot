import os
import sqlite3
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatMemberHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("8264725400:AAETEaBSsNana0hfk-igE3oq0vj_qcpLihY")

# Database setup
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS temp_users (user_id INTEGER, join_time TEXT)")
conn.commit()

scheduler = BackgroundScheduler()
scheduler.start()

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.chat_member.new_chat_members:
        user_id = member.id
        join_time = datetime.now()
        cursor.execute("INSERT INTO temp_users (user_id, join_time) VALUES (?, ?)", (user_id, str(join_time)))
        conn.commit()

async def check_and_ban(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    cursor.execute("SELECT user_id, join_time FROM temp_users")
    rows = cursor.fetchall()

    for user_id, join_time_str in rows:
        join_time = datetime.fromisoformat(join_time_str)
        if now >= join_time + timedelta(minutes=5):
            try:
                await context.bot.ban_chat_member(context.job.chat_id, user_id)
                cursor.execute("DELETE FROM temp_users WHERE user_id = ?", (user_id,))
                conn.commit()
            except:
                pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Anti Join AutoBan Bot Activated!")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(ChatMemberHandler(new_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(ChatMemberHandler(new_member, ChatMemberHandler.MY_CHAT_MEMBER))

    scheduler.add_job(check_and_ban, "interval", minutes=1, args=[app])

    app.run_polling()

if __name__ == "__main__":
    main()
