import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
import asyncio

# Démarre keep_alive
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
bot = commands.Bot(command_prefix="GZ.", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")


# Fonction principale pour charger l’extension
async def main():
    async with bot:
        try:
            await bot.load_extension("moderation")
            print("✅ Extension 'moderation' chargée avec succès.")
        except Exception as e:
            print(
                f"❌ Erreur lors du chargement de l'extension 'moderation' : {e}"
            )
        await bot.start(token)


# Démarrage du bot
asyncio.run(main())
