import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------
# 1. Environment Variables Configuration
# ----------------------------------------------------
MONGO_URI = os.getenv("MONGO_URI")
API_ID = os.getenv("API_ID")         # Back4App env vars mein daalein
API_HASH = os.getenv("API_HASH")     # Back4App env vars mein daalein
BOT_TOKEN = os.getenv("BOT_TOKEN")   # Back4App env vars mein daalein

# MongoDB Client Setup
mongo_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = mongo_client["my_telegram_bot_db"]

# Pyrogram Bot Client Setup
# (Apne zarurat ke hisaab se bot session name aur credentials set karein)
bot = Client(
    "my_bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ----------------------------------------------------
# 2. Pyrogram Bot Event Handlers (Example)
# ----------------------------------------------------
@bot.on_message()
async def handle_message(client, message):
    # Aapka Telegram bot ka saara logic yahan aayega
    logger.info(f"Received message from {message.from_user.id}")

# ----------------------------------------------------
# 3. Lifespan Manager (Non-Blocking Bot Startup)
# ----------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # App start hone par Telegram Bot background mein shuru hoga
    logger.info("Starting Telegram Bot in background...")
    try:
        await bot.start()
        logger.info("Telegram Bot Started Successfully!")
    except Exception as e:
        logger.error(f"Error starting Telegram Bot: {e}")
    
    yield  # FastAPI Server continues to listen for HTTP requests
    
    # App shutdown hone par Bot safely stop hoga
    logger.info("Stopping Telegram Bot...")
    try:
        await bot.stop()
        logger.info("Telegram Bot Stopped Successfully!")
    except Exception as e:
        logger.error(f"Error stopping Telegram Bot: {e}")

# FastAPI App Initialization
app = FastAPI(lifespan=lifespan)

# ----------------------------------------------------
# 4. HTTP Health Check Endpoint (Fixes 405 Method Error)
# ----------------------------------------------------
@app.get("/")
async def health_check():
    """
    Back4App deployment health checks use GET / to verify
    that the container is running and healthy.
    """
    return {
        "status": "healthy",
        "service": "Telegram Bot & Web API",
        "database": "Connected"
    }

# ----------------------------------------------------
# 5. Application Entry Point
# ----------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    # Back4App dynamic port assignment (Default 8080)
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app2:app", host="0.0.0.0", port=port, reload=False)
