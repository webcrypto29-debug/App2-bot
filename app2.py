import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI
import uvicorn

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8953998418:AAGeNgtWXGgEZzO-7HrtvwdL65Y5TVoDsPI")
API_ID = int(os.environ.get("API_ID", "1234567"))
API_HASH = os.environ.get("API_HASH", "abcdef1234567890abcdef1234567890")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456789"))
MONGO_URI = os.environ.get("MONGO_DB_URI", "")
DB_NAME = os.environ.get("DATABASE_NAME", "MyBot2DB")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://webcrypto29-debug.github.io/My-file-bot/index2.html")
PORT = int(os.environ.get("PORT", "8080"))

# --- FASTAPI SERVER FOR BACK4APP HEALTH CHECK ---
web_app = FastAPI()

@web_app.get("/")
@web_app.get("/health")
async def health_check():
    return {"status": "ok", "bot": "running"}

# --- DATABASE SETUP ---
if MONGO_URI:
    mongo_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = mongo_client[DB_NAME]
    users_col = db["users"]
    ads_col = db["ads_config"]
else:
    mongo_client = None
    db = None
    users_col = None
    ads_col = None

# --- BOT CLIENT ---
bot_client = Client(
    "bot2_advanced_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Initial Ads Setup in DB safely
async def init_ads_config():
    if ads_col is None:
        print("WARNING: MONGO_DB_URI is missing or invalid.")
        return
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
        print("Database connected and ads configuration initialized.")
    except Exception as e:
        print(f"Database connection failed: {e}")

# --- START COMMAND HANDLER ---
@bot_client.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "User"
    
    credits = 0
    if users_col is not None:
        try:
            user = await users_col.find_one({"_id": user_id})
            if not user:
                await users_col.insert_one({"_id": user_id, "username": username, "credits": 0})
            else:
                credits = user.get("credits", 0)
        except Exception as e:
            print(f"DB Error: {e}")

    # Verify Ad Completion
    if len(message.command) > 1 and message.command[1] == "VERIFY_AD":
        if users_col is not None:
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

# --- ADVANCED ADS CONTROL PANEL (ADMIN ONLY) ---
@bot_client.on_message(filters.command("ads") & filters.user(ADMIN_ID))
async def ads_control_panel(client: Client, message: Message):
    if ads_col is None:
        return await message.reply_text("❌ Database not connected.")
    
    config = await ads_col.find_one({"_id": "ads_setting"}) or {}
    
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

# --- CALLBACK HANDLER FOR TOGGLING ADS ---
@bot_client.on_callback_query(filters.regex("^toggle_"))
async def toggle_ad_status(client, callback_query):
    if callback_query.from_user.id != ADMIN_ID:
        return await callback_query.answer("Unauthorized!", show_alert=True)

    if ads_col is None:
        return await callback_query.answer("Database not connected!", show_alert=True)

    key_map = {
        "toggle_ad1": "ad1_status", "toggle_ad2": "ad2_status",
        "toggle_ad3": "ad3_status", "toggle_ad4": "ad4_status",
        "toggle_propush": "propush_status"
    }

    ad_key = key_map.get(callback_query.data)
    config = await ads_col.find_one({"_id": "ads_setting"}) or {}
    new_status = not config.get(ad_key, True)

    await ads_col.update_one({"_id": "ads_setting"}, {"$set": {ad_key: new_status}})
    await callback_query.answer(f"Updated! New status: {new_status}")
    
    await ads_control_panel(client, callback_query.message)

# --- ADMIN COMMANDS ---
@bot_client.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats_handler(client: Client, message: Message):
    if users_col is None:
        return await message.reply_text("❌ Database not connected.")
    total_users = await users_col.count_documents({})
    await message.reply_text(f"📊 **Bot Statistics:**\n\nकुल पंजीकृत यूज़र्स: `{total_users}`")

# --- MAIN RUNNER ---
async def start_services():
    try:
        await bot_client.start()
        print("Telegram Bot Started!")
    except Exception as e:
        print(f"Bot start failed: {e}")
    
    asyncio.create_task(init_ads_config())

async def main():
    await start_services()
    config = uvicorn.Config(web_app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
