import logging
import sqlite3
import time
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ChatMemberHandler,
    ContextTypes,
)

TOKEN = "8264725400:AAETEaBSsNana0hfk-igE3oq0vj_qcpLihY"
DB_FILE = "database.db"

logging.basicConfig(level=logging.INFO)

# Create database if not exists
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS pending_bans (
        user_id INTEGER,
        chat_id INTEGER,
        join_time INTEGER
    )
""")
conn.commit()


async def handle_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member
    status = member.new_chat_member.status

    # User JOINED
    if status in ("member", "restricted"):
        user_id = member.new_chat_member.user.id
        chat_id = update.effective_chat.id
        join_time = int(time.time())

        # Save to DB
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO pending_bans (user_id, chat_id, join_time) VALUES (?, ?, ?)",
                  (user_id, chat_id, join_time))
        conn.commit()
        conn.close()

        logging.info(f"Saved {user_id} for ban in 5 mins")


async def check_bans(context: ContextTypes.DEFAULT_TYPE):
    now = int(time.time())

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, chat_id, join_time FROM pending_bans")
    rows = c.fetchall()

    for user_id, chat_id, join_time in rows:
        if now - join_time >= 300:  # 5 minutes (300 seconds)
            try:
                await context.bot.ban_chat_member(chat_id, user_id)
                logging.info(f"BANNED: {user_id} from {chat_id}")
            except Exception as e:
                logging.error(e)

            c.execute("DELETE FROM pending_bans WHERE user_id=? AND chat_id=?", (user_id, chat_id))
            conn.commit()

    conn.close()


async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(ChatMemberHandler(handle_member, ChatMemberHandler.CHAT_MEMBER))

    # Run background check every 30 seconds
    application.job_queue.run_repeating(check_bans, interval=30, first=10)

    await application.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
