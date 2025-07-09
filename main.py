import discord
from discord.ext import commands

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="GZ.", intents=intents)

bot.user_gemmes = {}
bot.shop_channel_id = None

@bot.event
async def on_ready():
    print(f"{bot.user} est prêt !")

# ─── addgemmes ─────────────────────────────────────────
@commands.command()
async def addgemmes(ctx, membre: discord.Member, montant: int):
    if ctx.author.id != ctx.guild.owner_id:
        return await ctx.send("❌ Seul le créateur du serveur peut utiliser cette commande.")
    
    user_id = str(membre.id)
    bot.user_gemmes[user_id] = bot.user_gemmes.get(user_id, 0) + montant
    await ctx.send(f"✅ {montant} gemmes ont été ajoutées à {membre.mention}.")

# ─── set salon ─────────────────────────────────────────
@commands.command()
async def set(ctx, param: str, salon: discord.TextChannel):
    if ctx.author.id != ctx.guild.owner_id:
        return await ctx.send("❌ Seul le créateur du serveur peut utiliser cette commande.")
    
    if param.lower() == "salon":
        bot.shop_channel_id = salon.id
        await ctx.send(f"✅ Salon défini : {salon.mention}")
    else:
        await ctx.send("❌ Paramètre invalide. Utilise `GZ.set salon #salon`.")

# ─── shop ───────────────────────────────────────────────
class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎬 Edits Shorts", style=discord.ButtonStyle.blurple)
    async def shorts(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "**Edit pour des shorts :**\n"
            "• 1 clip : 80 gemmes 💎\n"
            "• 2 clips : 110 gemmes 💎\n"
            "• 1 clip (musique au choix) : 90 gemmes 💎\n"
            "• 2 clips (musique au choix) : 120 gemmes 💎",
            ephemeral=True)

    @discord.ui.button(label="🎮 Cache-Cache", style=discord.ButtonStyle.green)
    async def cache(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "**Vidéo cache-cache avec moi :**\n"
            "• 4 manches : 150 gemmes 💎\n"
            "• 6 manches : 200 gemmes 💎\n"
            "• 8 manches : 250 gemmes 💎",
            ephemeral=True)

    @discord.ui.button(label="🏆 Word Record", style=discord.ButtonStyle.red)
    async def wordrecord(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "**Word record :**\n"
            "• 1 essai : 100 gemmes 💎\n"
            "• 2 essais : 170 gemmes 💎\n"
            "• 3 essais : 230 gemmes 💎",
            ephemeral=True)

    @discord.ui.button(label="✨ Rôle esthétique", style=discord.ButtonStyle.gray)
    async def role(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "**Rôle esthétique :**\n"
            "• Rôle @@Ww (1 semaine) : 20 gemmes 💎\n"
            "• Rôle @@Ww (1 mois) : 50 gemmes 💎\n"
            "• Rôle @@Ww (permanent) : 100 gemmes 💎\n"
            "• Rôle personnalisé (ex: @Timcool_27) : 200 gemmes 💎",
            ephemeral=True)

@commands.command()
async def shop(ctx):
    await ctx.send("Voici les offres disponibles :", view=ShopView())

# ─── Enregistrer les commandes ─────────────────────────
bot.add_command(addgemmes)
bot.add_command(set)
bot.add_command(shop)

# ─── Lancer le bot ─────────────────────────────────────
bot.run("DISCORD_TOKEN")
