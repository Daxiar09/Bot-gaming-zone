import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
import asyncio

# Démarre le serveur web keep_alive (Replit/Render)
keep_alive()

# Charge les variables d’environnement
load_dotenv()
token = os.getenv("DISCORD_TOKEN")

# Intents nécessaires
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Création du bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    
    # Synchroniser les commandes slash une seule fois
    if not hasattr(bot, "synced"):
        bot.synced = True
        try:
            synced = await bot.tree.sync()
            print(f"✅ {len(synced)} commandes slash synchronisées.")
        except Exception as e:
            print(f"❌ Erreur de synchronisation : {e}")

# Fonction principale pour lancer le bot
async def main():
    async with bot:
        try:
            await bot.load_extension("moderation")  # Charge moderation.py
            print("✅ Extension 'moderation' chargée avec succès.")
        except Exception as e:
            print(f"❌ Erreur lors du chargement de l'extension 'moderation' : {e}")
        await bot.start(token)

# Démarre l'exécution
asyncio.run(main())
