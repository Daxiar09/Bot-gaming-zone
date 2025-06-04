import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
import json
import asyncio
from dotenv import load_dotenv
from keep_alive import keep_alive
import re

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} est connecté !")

async def main():
    keep_alive()
    await bot.load_extension("moderation") 
    await bot.start(token)

asyncio.run(main())
