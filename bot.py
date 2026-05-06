import os
import re
import time
import asyncio
import aiohttp
import aiofiles
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import API_ID, API_HASH, BOT_TOKEN
from terabox import TeraboxDownloader

# Bot Client Initialize
app = Client(
    "TeraboxDownloaderBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Terabox URL Patterns - All Domains
TERABOX_PATTERNS = [
    r"https?://(?:www\.)?terabox\.com/s/[\w-]+",
    r"https?://(?:www\.)?teraboxapp\.com/s/[\w-]+",
    r"https?://(?:www\.)?terasharelink\.com/s/[\w-]+",
    r"https?://(?:www\.)?1024tera\.com/s/[\w-]+",
    r"https?://(?:www\.)?4funbox\.com/s/[\w-]+",
    r"https?://(?:www\.)?mirrobox\.com/s/[\w-]+",
    r"https?://(?:www\.)?nephobox\.com/s/[\w-]+",
    r"https?://(?:www\.)?freeterabox\.com/s/[\w-]+",
    r"https?://(?:www\.)?1024terabox\.com/s/[\w-]+",
    r"https?://(?:www\.)?teraboxlink\.com/s/[\w-]+",
]

def is_terabox_link(url):
    """Check if URL is a valid Terabox link"""
    for pattern in TERABOX_PATTERNS:
        if re.match(pattern, url):
            return True
    return False

def format_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

def progress_bar(current, total):
    """Create progress bar"""
    percentage = current * 100 / total
    filled = int(percentage / 5)
    bar = "█" * filled + "░" * (20 - filled)
    return f"[{bar}] {percentage:.1f}%"

async def progress_callback(current, total, message, start_time, file_name):
    """Progress callback for uploads"""
    try:
        now = time.time()
        diff = now - start_time
        if diff < 1:
            return
        
        speed = current / diff
        eta = (total - current) / speed if speed > 0 else 0
        
        progress = progress_bar(current, total)
        text = f"""
📤 **Uploading...**

📁 **File:** `{file_name}`
📊 **Progress:** {progress}
📦 **Size:** {format_size(current)} / {format_size(total)}
⚡ **Speed:** {format_size(speed)}/s
⏱ **ETA:** {int(eta)}s
"""
        await message.edit_text(text)
    except Exception:
        pass

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Start command handler"""
    welcome_text = """
👋 **Terabox Downloader Bot-ലേക്ക് സ്വാഗതം!**

🔗 **Supported Domains:**
• terabox.com
• teraboxapp.com
• terasharelink.com
• 1024tera.com
• 4funbox.com
• mirrobox.com
• nephobox.com
• freeterabox.com
• 1024terabox.com
• teraboxlink.com

📝 **എങ്ങനെ ഉപയോഗിക്കാം:**
Terabox link അയക്കുക, ബോട്ട് file download ചെയ്ത് അയക്കും!

⚡ **Features:**
• No cookies needed
• No API required
• Large file support
• Fast downloads
• Progress tracking
"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/YourUsername")],
        [InlineKeyboardButton("📢 Channel", url="https://t.me/YourChannel")]
    ])
    
    await message.reply_text(welcome_text, reply_markup=keyboard)

@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Help command handler"""
    help_text = """
📚 **Help Menu**

**Commands:**
• /start - Bot start ചെയ്യാൻ
• /help - Help menu കാണാൻ
• /about - Bot-നെ കുറിച്ച്

**Usage:**
Simply Terabox link paste ചെയ്യുക!

**Supported Links:**
✅ terabox.com/s/xxxxx
✅ teraboxapp.com/s/xxxxx
✅ 1024tera.com/s/xxxxx
✅ മറ്റ് Terabox domains
"""
    await message.reply_text(help_text)

@app.on_message(filters.command("about"))
async def about_command(client: Client, message: Message):
    """About command handler"""
    about_text = """
🤖 **Terabox Downloader Bot**

**Version:** 2.0
**Language:** Python
**Framework:** Pyrogram

**Features:**
• Cookie-less downloading
• API-less operation
• Multiple domain support
• Large file handling
• Progress tracking
• Fast & reliable

Made with ❤️
"""
    await message.reply_text(about_text)

@app.on_message(filters.text & filters.private)
async def handle_link(client: Client, message: Message):
    """Handle Terabox links"""
    url = message.text.strip()
    
    # Check if valid Terabox link
    if not is_terabox_link(url):
        await message.reply_text("❌ **Invalid Link!**\n\nValid Terabox link അയക്കുക.")
        return
    
    # Send processing message
    status_msg = await message.reply_text("🔍 **Link processing...**\n\nPlease wait...")
    
    try:
        # Initialize downloader
        downloader = TeraboxDownloader()
        
        # Get file info
        await status_msg.edit_text("📡 **File info fetching...**")
        file_info = await downloader.get_file_info(url)
        
        if not file_info:
            await status_msg.edit_text("❌ **File info കിട്ടിയില്ല!**\n\nLink check ചെയ്യുക.")
            return
        
        file_name = file_info.get("file_name", "unknown_file")
        file_size = file_info.get("file_size", 0)
        download_url = file_info.get("download_url", "")
        
        if not download_url:
            await status_msg.edit_text("❌ **Download link കിട്ടിയില്ല!**")
            return
        
        # Show file info
        info_text = f"""
📁 **File Found!**

📝 **Name:** `{file_name}`
📦 **Size:** {format_size(file_size)}

⬇️ **Downloading started...**
"""
        await status_msg.edit_text(info_text)
        
        # Download file
        start_time = time.time()
        file_path = await downloader.download_file(
            download_url, 
            file_name,
            status_msg,
            start_time
        )
        
        if not file_path or not os.path.exists(file_path):
            await status_msg.edit_text("❌ **Download failed!**\n\nPlease try again.")
            return
        
        # Upload to Telegram
        await status_msg.edit_text("📤 **Uploading to Telegram...**")
        
        upload_start = time.time()
        
        # Check file size for upload method
        actual_size = os.path.getsize(file_path)
        
        if actual_size > 2000 * 1024 * 1024:  # > 2GB
            await status_msg.edit_text("❌ **File 2GB-യി�� കൂടുതൽ!**\n\nTelegram limit exceeded.")
            os.remove(file_path)
            return
        
        # Upload with progress
        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            file_name=file_name,
            caption=f"📁 **{file_name}**\n📦 Size: {format_size(actual_size)}",
            progress=progress_callback,
            progress_args=(status_msg, upload_start, file_name)
        )
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Success message
        success_text = f"""
✅ **Download Complete!**

📁 **File:** `{file_name}`
📦 **Size:** {format_size(actual_size)}
⏱ **Time:** {int(total_time)}s
"""
        await status_msg.edit_text(success_text)
        
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        await status_msg.edit_text(f"❌ **Error occurred!**\n\n`{str(e)}`")

# Run bot
if __name__ == "__main__":
    print("🤖 Bot Starting...")
    app.run()
