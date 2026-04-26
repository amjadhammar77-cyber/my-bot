import os
import asyncio
import tempfile
import re

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
# 🔑 8651496786:AAHjy0CNTtLXfrMT8c1YTTlFxdFEE-lizc8
# =============================================
BOT_TOKEN = "8651496786:AAHjy0CNTtLXfrMT8c1YTTlFxdFEE-lizc8"

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

def get_ydl_opts(audio_only: bool = False) -> dict:
    """
    Build yt-dlp options dynamically.
    Adds YouTube-specific fixes: browser headers, player_client fallbacks,
    and retries to bypass bot detection.
    """
    common = {
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        # Mimic a real browser to bypass YouTube bot checks
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
        # Use multiple YouTube clients as fallback
        "extractor_args": {
            "youtube": {
                "player_client": ["web", "android", "ios"],
            }
        },
        "retries": 5,
        "fragment_retries": 5,
        "ignoreerrors": False,
    }

    if audio_only:
        common.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }],
        })
    else:
        common.update({
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "max_filesize": 50 * 1024 * 1024,  # 50MB Telegram limit
            "postprocessors": [{
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }],
        })

    return common


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
    opts = get_ydl_opts(audio_only)
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if audio_only:
            base = os.path.splitext(filename)[0]
            mp3_path = base + ".mp3"
            if os.path.exists(mp3_path):
                return mp3_path
        if os.path.exists(filename):
            return filename
        video_id = info.get("id", "")
        ext = "mp3" if audio_only else "mp4"
        guessed = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")
        if os.path.exists(guessed):
            return guessed
    return None


# =============================================
# 💬 Bot commands
# =============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 *Welcome to the Video Downloader Bot!*\n\n"
        "📲 *How to use:*\n"
        "Just send a video link and I'll download it for you!\n\n"
        "✅ *Supported platforms:*\n"
        "🔴 YouTube\n"
        "📸 Instagram\n"
        "🎵 TikTok\n"
        "📘 Facebook\n"
        "🐦 Twitter / X\n"
        "🎮 Twitch\n"
        "🎬 Vimeo\n"
        "📺 Dailymotion\n"
        "🌐 And 1000+ other sites!\n\n"
        "📌 *Send a link now and choose: video or audio only?*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "❓ *Help*\n\n"
        "1️⃣ Copy a video link from any app\n"
        "2️⃣ Send it here\n"
        "3️⃣ Choose: 🎬 Video or 🎵 Audio only\n"
        "4️⃣ Wait a moment and the file will be sent!\n\n"
        "⚠️ *Note:* Maximum file size is 50MB\n\n"
        "🆘 If you have an issue, make sure the link is correct and the video is public (not private)"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# =============================================
# 🔗 Handle incoming links
# =============================================
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not is_supported_url(url):
        await update.message.reply_text(
            "❌ *Invalid link!*\n\n"
            "Make sure the URL starts with `http://` or `https://`\n"
            "and is from a supported platform 🌐",
            parse_mode="Markdown"
        )
        return

    context.user_data["pending_url"] = url

    keyboard = [
        [
            InlineKeyboardButton("🎬 Video", callback_data="dl_video"),
            InlineKeyboardButton("🎵 Audio", callback_data="dl_audio"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔗 *Link detected!*\n\nChoose download type:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


# =============================================
# 🎯 Handle button callbacks
# =============================================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get("pending_url")
    if not url:
        await query.edit_message_text("⚠️ Session expired. Please send the link again.")
        return

    audio_only = query.data == "dl_audio"
    mode_text = "🎵 Audio" if audio_only else "🎬 Video"

    # Show loading message
    loading_msg = await query.edit_message_text(
        f"⏳ *Downloading...*\n\n"
        f"📥 Fetching {mode_text} in the best available quality\n"
        f"Please wait a moment 🙏",
        parse_mode="Markdown"
    )

    try:
        loop = asyncio.get_event_loop()
        filepath = await loop.run_in_executor(
            None, download_media, url, audio_only
        )

        if not filepath or not os.path.exists(filepath):
            raise FileNotFoundError("File not found after download")

        # Delete loading message
        await loading_msg.delete()

        # Send the file
        if audio_only:
            await query.message.reply_audio(
                audio=open(filepath, "rb"),
                caption="🎵 *Downloaded successfully!*\n\nEnjoy listening 🎧",
                parse_mode="Markdown"
            )
        else:
            await query.message.reply_video(
                video=open(filepath, "rb"),
                caption="🎬 *Downloaded successfully!*\n\nEnjoy watching 🍿",
                parse_mode="Markdown",
                supports_streaming=True
            )

        # Clean up temp file
        os.remove(filepath)

    except Exception as e:
        error_msg = str(e)

        try:
            await loading_msg.delete()
        except Exception:
            pass

        if "File too large" in error_msg or "max_filesize" in error_msg.lower():
            user_error = (
                "⚠️ *File is too large!*\n\n"
                "Telegram's maximum allowed size is 50MB\n"
                "Try a shorter video or choose Audio Only 🎵"
            )
        elif "Private" in error_msg or "login" in error_msg.lower():
            user_error = (
                "🔒 *Video is private or requires login!*\n\n"
                "Make sure the video is public and not restricted 🌐"
            )
        elif "not available" in error_msg.lower() or "unavailable" in error_msg.lower():
            user_error = (
                "❌ *Video is unavailable!*\n\n"
                "It may have been deleted or removed from the platform 🗑️"
            )
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            user_error = (
                "🌐 *Connection error!*\n\n"
                "Check your internet connection and try again later 🔄"
            )
        else:
            user_error = (
                "❌ *Download failed!*\n\n"
                "Make sure the link is valid and the video is publicly accessible\n\n"
                "💡 Try again or send a different link"
            )

        await query.message.reply_text(user_error, parse_mode="Markdown")


# =============================================
# 🚀 Run the bot
# =============================================
def main():
    print("🤖 Starting the bot...")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("✅ Bot is running! Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()