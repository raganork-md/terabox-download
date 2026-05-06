import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from config import API_ID, API_HASH, BOT_TOKEN
from terabox import TeraboxDownloader

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Bot client
app = Client(
    "terabox_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Downloader instance
downloader = TeraboxDownloader()

# Start command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    text = """
🎬 **Terabox Downloader Bot**

ഹായ്! ഞാൻ Terabox files download ചെയ്യാൻ സഹായിക്കും!

**Supported Domains:**
• terabox.com
• teraboxapp.com  
• 1024tera.com
• freeterabox.com
• mirrobox.com
• nephobox.com
• 4funbox.com

**ഉപയോഗിക്കാൻ:**
Terabox link അയച്ചാൽ മതി! 🔗

Made with ❤️
"""
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# Help command
@app.on_message(filters.command("help") & filters.private)
async def help_cmd(client: Client, message: Message):
    text = """
📚 **Help**

**Commands:**
/start - Bot start ചെയ്യുക
/help - ഈ message

**How to use:**
1. Terabox link copy ചെയ്യുക
2. Bot-ലേക്ക് paste ചെയ്യുക
3. Download button click ചെയ്യുക

**Tips:**
• Valid terabox link ഉപയോഗിക്കുക
• Private files work ആകില്ല
"""
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# Handle terabox links
@app.on_message(filters.text & filters.private & ~filters.command(["start", "help"]))
async def handle_link(client: Client, message: Message):
    url = message.text.strip()
    
    # Validate URL
    if not downloader.is_valid_url(url):
        await message.reply_text("❌ Valid Terabox link അയക്കൂ!")
        return
    
    # Processing message
    status_msg = await message.reply_text("⏳ Processing link...")
    
    try:
        # Get file info
        info = await downloader.get_info(url)
        
        if "error" in info:
            await status_msg.edit_text(info["error"])
            return
        
        # Prepare response
        filename = info.get("filename", "Unknown")
        size = info.get("size", "Unknown")
        download_link = info.get("download_link", "")
        thumb = info.get("thumb", "")
        
        if not download_link:
            await status_msg.edit_text("❌ Download link കിട്ടിയില്ല!")
            return
        
        text = f"""
✅ **File Found!**

📁 **Name:** `{filename}`
📦 **Size:** {size}

⬇️ Download button click ചെയ്യുക!
"""
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬇️ Download", url=download_link)],
            [InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh:{url[:50]}")]
        ])
        
        # Send with thumbnail if available
        if thumb:
            try:
                await status_msg.delete()
                await message.reply_photo(
                    photo=thumb,
                    caption=text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                await status_msg.edit_text(text, reply_markup=buttons, parse_mode=ParseMode.MARKDOWN)
        else:
            await status_msg.edit_text(text, reply_markup=buttons, parse_mode=ParseMode.MARKDOWN)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await status_msg.edit_text(f"⚠️ Error: {str(e)}")

# Callback handler
@app.on_callback_query(filters.regex(r"^refresh:"))
async def refresh_callback(client, callback_query):
    await callback_query.answer("🔄 Link refresh ചെയ്യുക manually!")

# Main
async def main():
    logger.info("Starting bot...")
    await app.start()
    logger.info("Bot started successfully!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    app.run(main())
