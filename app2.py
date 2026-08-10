import os
import asyncio
from contextlib import asynccontextmanager
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI
import uvicorn

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8953998418:AAGeNgtWXGgEZzO-7HrtvwdL65Y5TVoDsPI")
API_ID = int(os.environ.get("API_ID", "31367866"))
API_HASH = os.environ.get("API_HASH", "575b2840f685a037000ead32cde239e1")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "6860017124"))

# NEW MONODB URI UPDATED HERE
MONGO_URI = os.environ.get(
    "MONGO_DB_URI", 
    "mongodb+srv://hyugvbbjiiuh_db_user:xETYAY8SQFQNMZoe@cluster0.rnxrb52.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
DB_NAME = os.environ.get("DATABASE_NAME", "MyBot2DB")

WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://webcrypto29-debug.github.io/My-file-bot/index.html")
PORT = int(os.environ.get("PORT", "8080"))

# --- DATABASE SETUP ---
mongo_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = mongo_client[DB_NAME]
users_col = db["users"]
ads_col = db["ads_config"]

# --- BOT CLIENT ---
bot_client = Client(
    "bot2_advanced_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Database Initial Config Setup
async def init_ads_config():
    try:
        default_config = {
            "_id": "ads_setting",
            "ad1_status": True, "ad1_code": "<!-- AD 1 SCRIPT HERE -->",
            "ad2_status": True, "ad2_code": "<!-- AD 2 SCRIPT HERE -->",
            "ad3_status": True, "ad3_code": "<!-- AD 3 SCRIPT HERE -->",
            "ad4_status": True, "ad4_code": "<!-- AD 4 SCRIPT HERE -->",
            "propush_status": True, "propush_code": "<script src='sw-check.js'></script>"
        }
        await asyncio.wait_for(
            ads_col.update_one({"_id": "ads_setting"}, {"$setOnInsert": default_config}, upsert=True),
            timeout=5.0
        )
        print("Database connected and ads initialized.")
    except Exception as e:
        print(f"Database setup notice: {e}")

# --- FASTAPI LIFESPAN MANAGER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Telegram Bot...")
    try:
        await bot_client.start()
        print("Telegram Bot Started Successfully!")
        asyncio.create_task(init_ads_config())
    except Exception as e:
        print(f"Failed to start bot: {e}")
    
    yield
    
    print("Stopping Telegram Bot...")
    try:
        await bot_client.stop()
    except Exception as e:
        print(f"Error stopping bot: {e}")

# --- FASTAPI APP ---
web_app = FastAPI(lifespan=lifespan)

@web_app.get("/")
@web_app.get("/health")
async def health_check():
    return {"status": "ok", "bot": "running"}

# --- BOT HANDLERS ---
@bot_client.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "User"
    
    credits = 0
    try:
        user = await users_col.find_one({"_id": user_id})
        if not user:
            await users_col.insert_one({"_id": user_id, "username": username, "credits": 0})
        else:
            credits = user.get("credits", 0)
    except Exception as e:
        print(f"DB Error: {e}")

    if len(message.command) > 1 and message.command[1] == "VERIFY_AD":
        try:
            await users_col.update_one({"_id": user_id}, {"$inc": {"credits": 3}})
            updated_user = await users_col.find_one({"_id": user_id})
            credits = updated_user.get('credits', 0) if updated_user else credits + 3
        except Exception as e:
            print(f"DB Error: {e}")
        
        await message.reply_text(
            f"🎉 **Ad Verified Successfully!**\n\n"
            f"आपको **+3 Credits** मिल चुके हैं।\n"
            f"💳 कुल बैलेंस: **{credits} Credits**\n\n"
            f"📁 आपकी फ़ाइल अनलॉक हो चुकी है!"
        )
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Watch Ad & Get File", web_app={"url": WEBAPP_URL})]
    ])

    await message.reply_text(
        f"नमस्ते **{message.from_user.first_name}**! 👋\n\n"
        f"अपनी फाइलों को अनलॉक करने के लिए नीचे दिए गए बटन पर क्लिक करें।\n\n"
        f"💳 बैलेंस: **{credits} Credits**",
        reply_markup=keyboard
    )

@bot_client.on_message(filters.command("ads") & filters.user(ADMIN_ID))
async def ads_control_panel(client: Client, message: Message):
    try:
        config = await ads_col.find_one({"_id": "ads_setting"}) or {}
    except Exception:
        config = {}
    
    def status_text(val): return "🟢 ON" if val else "🔴 OFF"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"Top Ad 1: {status_text(config.get('ad1_status'))}", callback_data="toggle_ad1"),
            InlineKeyboardButton(f"Bottom Ad 2: {status_text(config.get('ad2_status'))}", callback_data="toggle_ad2")
        ],
        [
            InlineKeyboardButton(f"Top Ad 3: {status_text(config.get('ad3_status'))}", callback_data="toggle_ad3"),
            InlineKeyboardButton(f"Bottom Ad 4: {status_text(config.get('ad4_status'))}", callback_data="toggle_ad4")
        ],
        [
            InlineKeyboardButton(f"ProPush Ads: {status_text(config.get('propush_status'))}", callback_data="toggle_propush")
        ]
    ])

    await message.reply_text(
        "⚙️ **ADVANCED AD CONTROL PANEL**\n\n"
        "आप यहाँ से Mini App के ऐड्स ऑन/ऑफ कर सकते हैं:",
        reply_markup=keyboard
    )

@bot_client.on_callback_query(filters.regex("^toggle_"))
async def toggle_ad_status(client, callback_query):
    await callback_query.answer("Processing...", show_alert=False)

    if callback_query.from_user.id != ADMIN_ID:
        return await callback_query.answer("Unauthorized!", show_alert=True)

    key_map = {
        "toggle_ad1": "ad1_status", "toggle_ad2": "ad2_status",
        "toggle_ad3": "ad3_status", "toggle_ad4": "ad4_status",
        "toggle_propush": "propush_status"
    }

    ad_key = key_map.get(callback_query.data)
    config = await ads_col.find_one({"_id": "ads_setting"}) or {}
    new_status = not config.get(ad_key, True)

    await ads_col.update_one({"_id": "ads_setting"}, {"$set": {ad_key: new_status}})
    await ads_control_panel(client, callback_query.message)

@bot_client.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats_handler(client: Client, message: Message):
    total_users = await users_col.count_documents({})
    await message.reply_text(f"📊 **Bot Statistics:**\n\nकुल पंजीकृत यूज़र्स: `{total_users}`")

if __name__ == "__main__":
    uvicorn.run("app2:web_app", host="0.0.0.0", port=PORT, log_level="info")
