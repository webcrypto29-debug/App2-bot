import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from motor.motor_asyncio import AsyncIOMotorClient

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8953998418:AAGeNgtWXGgEZzO-7HrtvwdL65Y5TVoDsPI")
API_ID = int(os.environ.get("API_ID", "1234567"))
API_HASH = os.environ.get("API_HASH", "abcdef1234567890abcdef1234567890")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456789"))
MONGO_URI = os.environ.get("MONGO_DB_URI", "YOUR_MONGO_DB_URI_HERE")
DB_NAME = os.environ.get("DATABASE_NAME", "MyBot2DB")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://webcrypto29-debug.github.io/My-file-bot/index2.html")

# --- DATABASE SETUP ---
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client[DB_NAME]
users_col = db["users"]
ads_col = db["ads_config"]  # Dynamic Ads Control Collection

# --- BOT CLIENT ---
app = Client(
    "bot2_advanced_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Initial Ads Setup in DB
async def init_ads_config():
    default_config = {
        "_id": "ads_setting",
        "ad1_status": True, "ad1_code": "<!-- AD 1 SCRIPT HERE -->",
        "ad2_status": True, "ad2_code": "<!-- AD 2 SCRIPT HERE -->",
        "ad3_status": True, "ad3_code": "<!-- AD 3 SCRIPT HERE -->",
        "ad4_status": True, "ad4_code": "<!-- AD 4 SCRIPT HERE -->",
        "propush_status": True, "propush_code": "<script src='sw-check.js'></script>"
    }
    await ads_col.update_one({"_id": "ads_setting"}, {"$setOnInsert": default_config}, upsert=True)

# --- START COMMAND ---
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "User"
    
    user = await users_col.find_one({"_id": user_id})
    if not user:
        await users_col.insert_one({"_id": user_id, "username": username, "credits": 0})
        user = {"credits": 0}

    # Verify Ad Completion
    if len(message.command) > 1 and message.command[1] == "VERIFY_AD":
        await users_col.update_one({"_id": user_id}, {"$inc": {"credits": 3}})
        updated_user = await users_col.find_one({"_id": user_id})
        
        await message.reply_text(
            f"🎉 **Ad Verified Successfully!**\n\n"
            f"आपको **+3 Credits** मिल चुके हैं।\n"
            f"💳 कुल बैलेंस: **{updated_user.get('credits', 0)} Credits**\n\n"
            f"📁 आपकी फ़ाइल अनलॉक हो चुकी है!"
        )
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Watch Ad & Get File", web_app={"url": WEBAPP_URL})]
    ])

    await message.reply_text(
        f"नमस्ते **{message.from_user.first_name}**! 👋\n\n"
        f"अपनी फाइलों को अनलॉक करने के लिए नीचे दिए गए बटन पर क्लिक करें।\n\n"
        f"💳 बैलेंस: **{user.get('credits', 0)} Credits**",
        reply_markup=keyboard
    )

# --- ADVANCED ADS CONTROL PANEL (ADMIN ONLY) ---
@app.on_message(filters.command("ads") & filters.user(ADMIN_ID))
async def ads_control_panel(client: Client, message: Message):
    config = await ads_col.find_one({"_id": "ads_setting"})
    
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
        ],
        [
            InlineKeyboardButton("⚙️ API Endpoint for Front-End", callback_data="show_api_info")
        ]
    ])

    await message.reply_text(
        "⚙️ **ADVANCED AD CONTROL PANEL**\n\n"
        "आप यहाँ से Mini App के ऐड्स ऑन/ऑफ कर सकते हैं:",
        reply_markup=keyboard
    )

# --- CALLBACK HANDLER FOR TOGGLING ADS ---
@app.on_callback_query(filters.regex("^toggle_"))
async def toggle_ad_status(client, callback_query):
    if callback_query.from_user.id != ADMIN_ID:
        return await callback_query.answer("Unauthorized!", show_alert=True)

    key_map = {
        "toggle_ad1": "ad1_status", "toggle_ad2": "ad2_status",
        "toggle_ad3": "ad3_status", "toggle_ad4": "ad4_status",
        "toggle_propush": "propush_status"
    }

    ad_key = key_map.get(callback_query.data)
    config = await ads_col.find_one({"_id": "ads_setting"})
    new_status = not config.get(ad_key, True)

    await ads_col.update_one({"_id": "ads_setting"}, {"$set": {ad_key: new_status}})
    await callback_query.answer(f"Updated! New status: {new_status}")
    
    # Refresh panel
    await ads_control_panel(client, callback_query.message)

# --- ALL PREVIOUS BOT COMMANDS ---

# 1. Stats Command
@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats_handler(client: Client, message: Message):
    total_users = await users_col.count_documents({})
    await message.reply_text(f"📊 **Bot Statistics:**\n\nकुल पंजीकृत यूज़र्स: `{total_users}`")

# 2. Add/Remove Credits Command
@app.on_message(filters.command("setcredits") & filters.user(ADMIN_ID))
async def set_credits(client: Client, message: Message):
    try:
        args = message.text.split()
        target_user = int(args[1])
        amount = int(args[2])
        await users_col.update_one({"_id": target_user}, {"$set": {"credits": amount}}, upsert=True)
        await message.reply_text(f"✅ User `{target_user}` का क्रेडिट बदलकर `{amount}` कर दिया गया।")
    except Exception as e:
        await message.reply_text("❌ फॉर्मेट गलत है! सही तरीका: `/setcredits <user_id> <amount>`")

# 3. Broadcast Command
@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID))
async def broadcast_msg(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("❌ किसी मैसेज को रीप्लाई करके `/broadcast` लिखें।")
    
    users = users_col.find({})
    success, failed = 0, 0
    await message.reply_text("📢 ब्रॉडकास्ट शुरू हो रहा है...")

    async for user in users:
        try:
            await message.reply_to_message.copy(chat_id=user["_id"])
            success += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1

    await message.reply_text(f"✅ **ब्रॉडकास्ट पूरा हुआ!**\n\nसफल: `{success}`\nविफल: `{failed}`")

# --- RUN BOT ---
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_ads_config())
    print("Bot 2 running with Full Control!")
    app.run()
