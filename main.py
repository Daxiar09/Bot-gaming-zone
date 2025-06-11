import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
import asyncio

keep_alive()
load_dotenv()
token = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")


async def main():
    async with bot:
        try:
            await bot.load_extension("moderation")
            print("✅ Extension 'moderation' chargée avec succès.")
        except Exception as e:
            print(f"❌ Erreur lors du chargement : {e}")
        await bot.start(token)


asyncio.run(main())
