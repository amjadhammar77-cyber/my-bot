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

# =============================================
# 🔑 8651496786:AAGj9Hvg2VXdika0xQC204L0-g

gG16RsW-4
# =============================================
BOT_TOKEN = os.environ.get("8651496786:AAGj9Hvg2VXdika0xQC204L0-g

gG16RsW-4")

# =============================================
# 🌐 Supported domains
# =============================================
SUPPORTED_DOMAINS = [
    "youtube.com", "youtu.be",
    "instagram.com",
    "tiktok.com", "vm.tiktok.com",
    "facebook.com", "fb.watch", "fb.com",
    "twitter.com", "x.com", "t.co",
    "reddit.com",
    "twitch.tv",
    "vimeo.com",
    "dailymotion.com",
    "pinterest.com",
    "linkedin.com",
    "snapchat.com",
    "triller.co",
    "rumble.com",
    "bilibili.com",
    "ok.ru",
    "vk.com",
    "streamable.com",
    "gfycat.com",
    "imgur.com",
    "medal.tv",
    "kick.com",
]

# =============================================
# ⚙️ Download settings
# =============================================
DOWNLOAD_DIR = tempfile.gettempdir()

YDL_VIDEO_OPTS = {
    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "merge_output_format": "mp4",
    "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "max_filesize": 50 * 1024 * 1024,
    "postprocessors": [{
        "key": "FFmpegVideoConvertor",
        "preferedformat": "mp4",
    }],
}

YDL_AUDIO_OPTS = {
    "format": "bestaudio/best",
    "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "320",
    }],
}

# =============================================
# 🔍 URL validation
# =============================================
def is_supported_url(url: str) -> bool:
    pattern = r'https?://[^\s]+'
    if not re.match(pattern, url.strip()):
        return False
    for domain in SUPPORTED_DOMAINS:
        if domain in url:
            return True
    return url.startswith("http")

# =============================================
# 📥 Download function
# =============================================
def download_media(url: str, audio_only: bool = False) -> str | None:
    opts = YDL_AUDIO_OPTS.copy() if audio_only
