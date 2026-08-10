import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables Read Karein
MONGO_URI = os.getenv("MONGO_URI")
API_ID_ENV = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# API_ID ko integer mein parse karein
API_ID = int(API_ID_ENV) if API_ID_ENV and API_ID_ENV.isdigit() else None

# MongoDB Client
mongo_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = mongo_client["my_telegram_bot_db"]

# Bot Client Setup
bot = None
if API_ID and API_HASH and BOT_TOKEN:
    bot = Client(
        "my_bot_session",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )
else:
    logger.error("Missing required variables: API_ID, API_HASH, or BOT_TOKEN!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    if bot:
        logger.info("Starting Telegram Bot...")
        try:
            await bot.start()
            logger.info("Telegram Bot Started Successfully!")
        except Exception as e:
            logger.error(f"Error starting Telegram Bot: {e}")
    yield
    if bot:
        logger.info("Stopping Telegram Bot...")
        try:
            await bot.stop()
        except Exception as e:
            logger.error(f"Error stopping Telegram Bot: {e}")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Bot Server Running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app2:app", host="0.0.0.0", port=port)
