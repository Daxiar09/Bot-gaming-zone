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
bot = commands.Bot(command_prefix=".", intents=intents)
tree = bot.tree


@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    try:
        synced = await tree.sync()
        print(f'Slash commands synchronisées : {len(synced)}')
    except Exception as e:
        print(f'Erreur de synchronisation : {e}')


#  préfixe .
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'Latence : {latency} ms')


# slash
@tree.command(name="ping", description="Vérifie la latence du bot")
async def slash_ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'Latence : {latency} ms')


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

#lien : https://discord.com/oauth2/authorize?client_id=1379151294677385258&permissions=268446848&scope=bot+applications.commands
