import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
import asyncio

# Lance le serveur web (Replit / Render)
keep_alive()

# Charge les variables d’environnement (token)
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

    # Synchroniser les commandes slash
    if not hasattr(bot, "synced"):
        bot.synced = True
        try:
            synced = await bot.tree.sync()
            print(f"✅ {len(synced)} commandes slash synchronisées.")
        except Exception as e:
            print(f"❌ Erreur de synchronisation des commandes : {e}")


async def main():
    async with bot:
        try:
            await bot.load_extension("moderation")
            print("✅ Extension 'moderation' chargée avec succès.")
        except Exception as e:
            print(f"❌ Erreur de chargement de l'extension 'moderation' : {e}")

        await bot.start(token)


# Démarrage du bot
asyncio.run(main())
