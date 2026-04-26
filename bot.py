import os
import asyncio
import tempfile
import re
import threading

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import yt_dlp

# 🔑 اقرأ التوكن من المتغيرات (لا تضعه هنا)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

SUPPORTED_DOMAINS = [
    "youtube.com","youtu.be","instagram.com","tiktok.com","vm.tiktok.com",
    "facebook.com","fb.watch","fb.com","twitter.com","x.com","t.co",
    "reddit.com","twitch.tv","vimeo.com","dailymotion.com","pinterest.com",
    "linkedin.com","snapchat.com","triller.co","rumble.com","bilibili.com",
    "ok.ru","vk.com","streamable.com","gfycat.com","imgur.com","medal.tv","kick.com",
]

DOWNLOAD_DIR = tempfile.gettempdir()

YDL_VIDEO_OPTS = {
    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
    "merge_output_format": "mp4",
    "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
    "quiet": True,
    "noplaylist": True,
}

YDL_AUDIO_OPTS = {
    "format": "bestaudio/best",
    "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
    "quiet": True,
    "noplaylist": True,
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
    }],
}

def is_supported_url(url: str) -> bool:
    return url.startswith("http")

def download_media(url, audio_only=False):
    opts = YDL_AUDIO_OPTS.copy() if audio_only else YDL_VIDEO_OPTS.copy()
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send link 🎬")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    context.user_data["url"] = url

    keyboard = [[
        InlineKeyboardButton("Video", callback_data="v"),
        InlineKeyboardButton("Audio", callback_data="a"),
    ]]
    await update.message.reply_text("Choose:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get("url")
    audio_only = query.data == "a"

    msg = await query.edit_message_text("Downloading...")

    try:
        loop = asyncio.get_event_loop()
        path = await loop.run_in_executor(None, download_media, url, audio_only)

        await msg.delete()

        if audio_only:
            await query.message.reply_audio(audio=open(path, "rb"))
        else:
            await query.message.reply_video(video=open(path, "rb"))

        os.remove(path)
    except:
        await msg.delete()
        await query.message.reply_text("Error ❌")

# Flask server (مهم لـ Railway)
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot running"

def run_web():
    port = int(os.environ.get("PORT", 3000))
    flask_app.run(host="0.0.0.0", port=port)

async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN missing")

    threading.Thread(target=run_web).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(handle_callback))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(1000)

if __name__ == "__main__":
    asyncio.run(main())
