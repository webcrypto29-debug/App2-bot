import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters
from pyrogram.types import Message

# Logging Config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------
# 1. Environment Variables Configuration
# ----------------------------------------------------
MONGO_URI = os.getenv("MONGO_URI")
API_ID_ENV = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Convert API_ID to integer safely
API_ID = int(API_ID_ENV) if API_ID_ENV and API_ID_ENV.isdigit() else None

# MongoDB Connection Setup
mongo_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000) if MONGO_URI else None
db = mongo_client["my_telegram_bot_db"] if mongo_client else None

# Pyrogram Client Setup
bot = None
if API_ID and API_HASH and BOT_TOKEN:
    bot = Client(
        "my_bot_session",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )
else:
    logger.error("Missing credentials! Check API_ID, API_HASH, or BOT_TOKEN in Back4App settings.")

# ----------------------------------------------------
# 2. Telegram Bot Command Handlers
# ----------------------------------------------------
if bot:
    @bot.on_message(filters.command("start") & filters.private)
    async def start_command(client: Client, message: Message):
        """
        Jab user Telegram par /start bhejega tab yeh reply karega
        """
        logger.info(f"Received /start from {message.from_user.id}")
        await message.reply_text("Hello! Bot active aur chal raha hai. Aapka welcome hai! 🚀")

    @bot.on_message(filters.command("genlink") & filters.private)
    async def genlink_command(client: Client, message: Message):
        logger.info(f"Received /genlink from {message.from_user.id}")
        await message.reply_text("Link Generation feature active hai.")

# ----------------------------------------------------
# 3. Lifespan Manager (Background Startup)
# ----------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    if bot:
        logger.info("Starting Telegram Bot...")
        try:
            await bot.start()
            logger.info("Telegram Bot Started Successfully!")
        except Exception as e:
            logger.error(f"Failed to start Telegram Bot: {e}")
    yield
    if bot:
        logger.info("Stopping Telegram Bot...")
        try:
            await bot.stop()
        except Exception as e:
            logger.error(f"Error stopping Telegram Bot: {e}")

# FastAPI App
app = FastAPI(lifespan=lifespan)

# Back4App Health Check Endpoint (Fixes 405 error)
@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Bot & FastAPI Server running smoothly!"}

# Entrypoint
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app2:app", host="0.0.0.0", port=port)
