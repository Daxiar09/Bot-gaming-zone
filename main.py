import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
import asyncio

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Intents nécessaires
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Créer le bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()  # 🔁 synchronise les commandes
    print(f"{bot.user} est prêt.")
      
# Lancer le bot
async def main():
    await bot.load_extension("moderation")
    await bot.start(TOKEN)


asyncio.run(main())
