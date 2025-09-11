import discord
from discord.ext import commands
import os
import traceback
import sys
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if os.path.exists(".env"):
    load_dotenv()
else:
    logger.warning("⚠️ .env file not found. Ensure DISCORD_TOKEN is set.")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables")

extensions = [
    "cogs.spamCommands",
]

# Initialize Discord bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'✅ {bot.user} has connected to Discord!')
    
    # Load extensions
    for extension in extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f'✅ Loaded extension: {extension}')
        except Exception as e:
            logger.error(f'❌ Failed to load extension {extension}: {e}')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f'✅ Synced {len(synced)} command(s)')
    except Exception as e:
        logger.error(f'❌ Failed to sync commands: {e}')

if __name__ == "__main__":
    try:
        bot.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        logger.error("❌ Invalid Discord token")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping bot...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"⚠️ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)