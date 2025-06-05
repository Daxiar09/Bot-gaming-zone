import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
import asyncio

keep_alive()

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()  # Synchronise les commandes slash avec Discord
    print(f"{bot.user} est connecté ! Les commandes slash sont synchronisées.")


async def main():
    async with bot:
        await bot.load_extension("moderation"
                                 )  # Charge ton fichier moderation.py
        await bot.start(token)


asyncio.run(main())
