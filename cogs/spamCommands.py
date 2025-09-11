import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from datetime import datetime
import json
import os
import asyncio

CONFIG_FILE = "spam_channels.json"

class SpamCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "http://like2.vercel.app/send_requests"
        self.session = aiohttp.ClientSession()
        self.config_data = self.load_config()
        self.cooldowns = {}

    def is_server_subscribed(self, guild_id):
        return False  # Placeholder: Implement subscription logic

    def is_limit_reached(self, guild_id):
        return False  # Placeholder: Implement limit logic

    def check_request_limit(self, guild_id):
        try:
            return self.is_server_subscribed(guild_id) or not self.is_limit_reached(guild_id)
        except Exception as e:
            print(f"Error checking request limit: {e}")
            return False

    def load_config(self):
        default_config = {
            "servers": {},
            "global_settings": {
                "default_all_channels": False,
                "default_cooldown": 30,
                "default_daily_limit": 30
            }
        }

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    loaded_config = json.load(f)
                    loaded_config.setdefault("global_settings", {})
                    loaded_config["global_settings"].setdefault("default_all_channels", False)
                    loaded_config["global_settings"].setdefault("default_cooldown", 30)
                    loaded_config["global_settings"].setdefault("default_daily_limit", 30)
                    loaded_config.setdefault("servers", {})
                    return loaded_config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}")
                return default_config
        return default_config

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving config: {e}")

    async def is_channel_allowed(self, ctx):
        try:
            guild_id = str(ctx.guild.id)
            if guild_id not in self.config_data["servers"] or not self.config_data["servers"][guild_id].get("spam_channels"):
                return False
            allowed_channels = self.config_data["servers"][guild_id].get("spam_channels", [])
            return str(ctx.channel.id) in allowed_channels
        except Exception as e:
            print(f"Error checking channel permission: {e}")
            return False

    @commands.hybrid_command(name="setspamchannel", description="Allow a channel for !spam commands")
    @commands.has_permissions(administrator=True)
    async def set_spam_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        # Validate that the channel is a valid TextChannel and accessible
        if not isinstance(channel, discord.TextChannel):
            embed = discord.Embed(
                title="❌ Invalid Channel",
                description="Please provide a valid text channel (e.g., #channel-name or channel ID).",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed, ephemeral=True)

        # Check if the bot can view the channel
        if not channel.permissions_for(ctx.guild.me).view_channel:
            embed = discord.Embed(
                title="❌ Cannot Access Channel",
                description=f"I don't have permission to view {channel.mention}. Please ensure I have the 'View Channel' permission.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed, ephemeral=True)

        guild_id = str(ctx.guild.id)
        self.config_data["servers"].setdefault(guild_id, {"spam_channels": [], "config": {}})
        if str(channel.id) not in self.config_data["servers"][guild_id]["spam_channels"]:
            self.config_data["servers"][guild_id]["spam_channels"].append(str(channel.id))
            self.save_config()
            await ctx.send(f"✅ {channel.mention} is now allowed for `/spam` commands")
        else:
            await ctx.send(f"ℹ️ {channel.mention} is already allowed for `/spam` commands")

    @commands.hybrid_command(name="removespamchannel", description="Remove a channel from !spam commands")
    @commands.has_permissions(administrator=True)
    async def remove_spam_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        # Validate that the channel is a valid TextChannel
        if not isinstance(channel, discord.TextChannel):
            embed = discord.Embed(
                title="❌ Invalid Channel",
                description="Please provide a valid text channel (e.g., #channel-name or channel ID).",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed, ephemeral=True)

        guild_id = str(ctx.guild.id)
        if guild_id in self.config_data["servers"]:
            if str(channel.id) in self.config_data["servers"][guild_id]["spam_channels"]:
                self.config_data["servers"][guild_id]["spam_channels"].remove(str(channel.id))
                self.save_config()
                await ctx.send(f"✅ {channel.mention} has been removed from allowed channels")
            else:
                await ctx.send(f"❌ {channel.mention} is not in the list of allowed channels")
        else:
            await ctx.send("ℹ️ This server has no saved configuration")

    @commands.hybrid_command(name="spamchannels", description="List allowed channels for spam commands")
    async def list_spam_channels(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)

        if guild_id in self.config_data["servers"] and self.config_data["servers"][guild_id]["spam_channels"]:
            channels = []
            for channel_id in self.config_data["servers"][guild_id]["spam_channels"]:
                channel = ctx.guild.get_channel(int(channel_id))
                channels.append(f"• {channel.mention if channel else f'ID: {channel_id} (not found)'}")

            embed = discord.Embed(
                title="Allowed channels for !spam",
                description="\n".join(channels),
                color=discord.Color.blue()
            )
            cooldown = self.config_data["servers"][guild_id]["config"].get("cooldown", self.config_data["global_settings"]["default_cooldown"])
            embed.set_footer(text=f"Current cooldown: {cooldown} seconds")
        else:
            embed = discord.Embed(
                title="Allowed channels for !spam",
                description="No channels are configured. Use `!setspamchannel` to allow specific channels.",
                color=discord.Color.red()
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="spam", description="Send spam requests to a Free Fire player")
    @app_commands.describe(uid="FREE FIRE UID", server="Server name (e.g. BD, SG, BR, IND, US, EUROPE, etc.)")
    async def spam_player(self, ctx, uid: str, server: str):
        guild_id = str(ctx.guild.id)

        # Check if channel is allowed
        if not await self.is_channel_allowed(ctx):
            embed = discord.Embed(
                title="❌ Command Not Allowed",
                description=f"This command can only be used in channels configured for `!spam`. Use `!setspamchannel {ctx.channel.mention}` to allow this channel.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed, ephemeral=True)

        # Validate UID
        if not uid.isdigit() or len(uid) < 6:
            return await ctx.reply(
                "Invalid UID! It must:\n- Be only numbers\n- Have at least 6 digits",
                mention_author=False,
                ephemeral=True
            )

        # Validate Server
        valid_servers = ["BD", "SG", "BR", "IND", "US", "EUROPE"]
        if not server or server.upper() not in valid_servers:
            return await ctx.reply(
                f"❌ Please provide a valid server name!\nExample: {', '.join(valid_servers)}",
                mention_author=False,
                ephemeral=True
            )

        # Handle cooldown
        cooldown = self.config_data["global_settings"]["default_cooldown"]
        if guild_id in self.config_data["servers"]:
            cooldown = self.config_data["servers"][guild_id]["config"].get("cooldown", cooldown)

        user_id = ctx.author.id
        current_time = datetime.now().timestamp()
        
        if user_id in self.cooldowns:
            time_left = self.cooldowns[user_id] + cooldown - current_time
            if time_left > 0:
                embed = discord.Embed(
                    title="⏰ Cooldown Active",
                    description=f"Please wait **{int(time_left)}** seconds before using this command again.",
                    color=discord.Color.orange()
                )
                return await ctx.send(embed=embed, ephemeral=True)

        # Set cooldown
        self.cooldowns[user_id] = current_time

        # Send initial response
        embed = discord.Embed(
            title="🔄 Processing Spam Request",
            description=f"Sending spam requests to UID: `{uid}` on server `{server.upper()}`...",
            color=discord.Color.yellow()
        )
        message = await ctx.send(embed=embed)

        try:
            # Make API request
            params = {
                "uid": uid,
                "server": server.upper(),
                "key": "rifat1122"
            }
            
            async with self.session.get(self.api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Create result embed
                    embed = discord.Embed(
                        title="📊 Spam Request Results",
                        color=discord.Color.green() if data.get("success_count", 0) > 0 else discord.Color.red()
                    )
                    
                    # Add player info
                    embed.add_field(
                        name="🎮 Player Information",
                        value=f"**Name:** {data.get('player', 'Unknown')}\n**UID:** `{uid}`\n**Server:** {server.upper()}",
                        inline=False
                    )
                    
                    # Add request results
                    embed.add_field(
                        name="📈 Request Statistics",
                        value=f"**✅ Successful:** {data.get('success_count', 0)}\n**❌ Failed:** {data.get('failed_count', 0)}\n**🔢 Total Tokens Used:** {data.get('total_tokens_used', 0)}",
                        inline=False
                    )
                    
                    # Add status info
                    status_text = {
                        0: "❌ Failed",
                        1: "✅ Success", 
                        2: "⚠️ Partial Success"
                    }.get(data.get('status', 0), "❓ Unknown")
                    
                    embed.add_field(
                        name="📋 Status Information",
                        value=f"**Status:** {status_text}\n**Timestamp:** {data.get('timestamp', 'Unknown')}",
                        inline=False
                    )
                    
                    # Set footer
                    embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
                    
                    await message.edit(embed=embed)
                    
                else:
                    embed = discord.Embed(
                        title="❌ API Error",
                        description=f"Failed to get response from spam API. Status code: {response.status}",
                        color=discord.Color.red()
                    )
                    await message.edit(embed=embed)
                    
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while processing the spam request: {str(e)}",
                color=discord.Color.red()
            )
            await message.edit(embed=embed)

    async def cog_unload(self):
        if hasattr(self, 'session'):
            await self.session.close()

async def setup(bot):
    await bot.add_cog(SpamCommands(bot))
