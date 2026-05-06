import os
import asyncio
import aiohttp
import aiofiles
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from terabox import TeraboxDownloader

bot = Client(
    "terabox_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

terabox = TeraboxDownloader()

@bot.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        "🎬 **Terabox Downloader Bot**\n\n"
        "📤 Terabox link അയക്കൂ, ഞാൻ download ചെയ്തു തരാം!\n\n"
        "✅ Supported: terabox.com, 1024tera.com, teraboxapp.com etc.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Developer", url="https://t.me/your_username")]
        ])
    )

@bot.on_message(filters.text & filters.private)
async def handle_link(client: Client, message: Message):
    url = message.text.strip()
    
    if not terabox.is_valid_url(url):
        return
    
    status_msg = await message.reply_text("⏳ **Processing...**\n\nFile info എടുക്കുന്നു...")
    
    try:
        info = await terabox.get_download_link(url)
        
        if "error" in info:
            await status_msg.edit_text(f"❌ **Error:** {info['error']}\n\n🔄 Link ശരിയാണോ എന്ന് check ചെയ്യൂ!")
            return
        
        filename = info.get("filename", "Unknown")
        size_str = info.get("size_str", "Unknown")
        size = info.get("size", 0)
        download_link = info.get("fast_link") or info.get("download_link")
        
        await status_msg.edit_text(
            f"📁 **File Found!**\n\n"
            f"📝 **Name:** `{filename}`\n"
            f"📊 **Size:** {size_str}\n\n"
            f"⬇️ Downloading..."
        )
        
        # Download file
        file_path = f"downloads/{filename}"
        os.makedirs("downloads", exist_ok=True)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.terabox.com/"
        }
        
        downloaded = 0
        async with aiohttp.ClientSession() as session:
            async with session.get(download_link, headers=headers, timeout=aiohttp.ClientTimeout(total=3600)) as resp:
                if resp.status != 200:
                    await status_msg.edit_text(f"❌ Download failed! Status: {resp.status}")
                    return
                
                async with aiofiles.open(file_path, 'wb') as f:
                    async for chunk in resp.content.iter_chunked(1024 * 1024):
                        await f.write(chunk)
                        downloaded += len(chunk)
                        percent = (downloaded / size * 100) if size > 0 else 0
                        
                        if downloaded % (5 * 1024 * 1024) == 0:
                            await status_msg.edit_text(
                                f"📁 **{filename}**\n"
                                f"📊 {size_str}\n\n"
                                f"⬇️ **Downloading:** {percent:.1f}%\n"
                                f"📥 {terabox._format_size(downloaded)} / {size_str}"
                            )
        
        await status_msg.edit_text(f"📤 **Uploading to Telegram...**\n\n📁 {filename}")
        
        # Upload to Telegram
        await message.reply_document(
            document=file_path,
            caption=f"📁 **{filename}**\n📊 **Size:** {size_str}\n\n🤖 @YourBotUsername",
            progress=progress_callback,
            progress_args=(status_msg, "Uploading")
        )
        
        await status_msg.delete()
        
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        await status_msg.edit_text(f"❌ **Error:** {str(e)}")

async def progress_callback(current, total, message, action):
    percent = current * 100 / total
    try:
        await message.edit_text(f"📤 **{action}:** {percent:.1f}%")
    except:
        pass

print("Bot Starting...")
bot.run()
