from dotenv import load_dotenv
load_dotenv()

import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# Silence unnecessary logs
logging.basicConfig(level=logging.WARNING)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Agent online! Send me a message or use /auto for autonomous tasks."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from First_AI_Agent import ask_claude
    user_text = update.message.text
    print(f"📨 Telegram: {user_text}")
    response = ask_claude(user_text)
    await update.message.reply_text(response)

async def handle_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from First_AI_Agent import tools, run_tool, anthropic_client
    from autonomous import run_autonomous_task
    goal = " ".join(context.args)
    if not goal:
        await update.message.reply_text("Please provide a goal. Example: /auto research AI news")
        return
    await update.message.reply_text(f"🤖 Starting autonomous task: {goal}")
    result = run_autonomous_task(goal, tools, run_tool, anthropic_client)
    await update.message.reply_text(result)

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("auto", handle_auto))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Telegram bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()