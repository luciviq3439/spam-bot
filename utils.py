import json
import os
import aiohttp
import asyncio
from dotenv import load_dotenv
import logging

load_dotenv()


# Set up logging
logger = logging.getLogger(__name__)

# Define guild config file
GUILD_CONFIG_FILE = "allowed_guilds.json"

def load_guild_config():
    default_config = {"allowed_guilds": {}}
    if os.path.exists(GUILD_CONFIG_FILE):
        try:
            with open(GUILD_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"Loaded guild config: {config}")
                return config
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading guild config from {GUILD_CONFIG_FILE}: {e}")
            return default_config
    else:
        logger.info(f"Creating new {GUILD_CONFIG_FILE}")
        save_guild_config(default_config)
        return default_config

def save_guild_config(config):
    try:
        with open(GUILD_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved guild config to {GUILD_CONFIG_FILE}: {config}")
    except IOError as e:
        logger.error(f"Error saving guild config to {GUILD_CONFIG_FILE}: {e}")
        raise


async def check_ban(uid: str) -> dict | None:
    api_url = f"https://checkban-vf40.onrender.com/ban?uid={uid}"
    timeout = aiohttp.ClientTimeout(total=20)  # 20 seconds total timeout

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url) as response:
                response.raise_for_status()
                response_data = await response.json()

                if response_data.get("status") == 200:
                    data = response_data.get("data")
                    if data:  # Ensure 'data' key exists and is not None
                        return {
                            "is_banned": data.get("is_banned", 0),
                            "nickname": data.get("nickname", ""),
                            "period": data.get("period", 0),
                            "last_login": data.get("last_login", 0),
                            "createAt": data.get("createAt", 0),
                            "region": data.get("region", 0)
                        }

                # If status is not 200 or data is missing, return None
                return None

    except aiohttp.ClientError as e:
        print(f"API request failed for UID {uid}: {e}")
        return None
    except asyncio.TimeoutError:
        print(f"API request timed out for UID {uid}.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred for UID {uid}: {e}")
        return None
