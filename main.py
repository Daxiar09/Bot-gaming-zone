import discord
from discord.ext import commands, tasks
from discord.utils import get
import asyncio
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="T.", intents=intents)

# Variables globales
bot.user_gemmes = {}
bot.shop_channel_id = None      # salon où les offres sont notifiées
bot.gemmes_channel_id = None    # salon où on affiche les gemmes
bot.gemmes_message_id = None    # message d'affichage des gemmes
CREATOR_ID = 1089542697108377621
ROLE_AWW_ID = 1386397029822890114
ROLE_TIMCOOL_ID = 1371083702028865538

# ----- Helper : check si auteur est créateur serveur -----
def is_guild_owner():
    async def predicate(ctx):
        return ctx.guild and ctx.author.id == ctx.guild.owner_id
    return commands.check(predicate)

# ----- Afficher ou mettre à jour le message des gemmes -----
async def update_gemmes_message():
    if not bot.gemmes_channel_id or not bot.gemmes_message_id:
        return
    channel = bot.get_channel(bot.gemmes_channel_id)
    if not channel:
        return
    try:
        msg = await channel.fetch_message(bot.gemmes_message_id)
    except:
        msg = None

    description = ""
    for user_id, gems in bot.user_gemmes.items():
        member = channel.guild.get_member(int(user_id))
        if member:
            description += f"{member.display_name} : {gems} 💎\n"
    if description == "":
        description = "Aucun membre avec des gemmes."

    embed = discord.Embed(title="💎 Gemmes des membres", description=description, color=0x00ff00)
    if msg:
        await msg.edit(embed=embed)
    else:
        msg = await channel.send(embed=embed)
        bot.gemmes_message_id = msg.id

# ----- Commandes -----

@bot.command()
@is_guild_owner()
async def addgemmes(ctx, membre: discord.Member, montant: int):
    user_id = str(membre.id)
    bot.user_gemmes[user_id] = bot.user_gemmes.get(user_id, 0) + montant
    await ctx.send(f"✅ {montant} gemmes ont été ajoutées à {membre.mention}.")
    await update_gemmes_message()

@bot.command()
@is_guild_owner()
async def deletegemmes(ctx, membre: discord.Member, montant: int):
    user_id = str(membre.id)
    current = bot.user_gemmes.get(user_id, 0)
    bot.user_gemmes[user_id] = max(0, current - montant)
    await ctx.send(f"✅ {montant} gemmes ont été retirées à {membre.mention}.")
    await update_gemmes_message()

@bot.command(name="set_salon_offres")
@is_guild_owner()
async def set_salon_offres(ctx, salon: discord.TextChannel):
    bot.shop_channel_id = salon.id
    await ctx.send(f"✅ Salon des offres défini sur {salon.mention}")

@bot.command(name="set_salon_gemmes")
@is_guild_owner()
async def set_salon_gemmes(ctx, salon: discord.TextChannel):
    bot.gemmes_channel_id = salon.id
    await ctx.send(f"✅ Salon des gemmes défini sur {salon.mention}")
    await update_gemmes_message()

# ----- View pour la boutique -----

class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎬 Edits Shorts", style=discord.ButtonStyle.blurple)
    async def shorts(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = (
            "**Edit pour des shorts :**\n"
            "• 1 clip : 80 gemmes 💎\n"
            "• 2 clips : 110 gemmes 💎\n"
            "• 1 clip (musique au choix) : 90 gemmes 💎\n"
            "• 2 clips (musique au choix) : 120 gemmes 💎"
        )
        await interaction.response.edit_message(content=desc, view=ShortsBuyView())

    @discord.ui.button(label="🎮 Cache-Cache", style=discord.ButtonStyle.green)
    async def cache(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = (
            "**Vidéo cache-cache avec moi :**\n"
            "• 4 manches : 150 gemmes 💎\n"
            "• 6 manches : 200 gemmes 💎\n"
            "• 8 manches : 250 gemmes 💎"
        )
        await interaction.response.edit_message(content=desc, view=CacheBuyView())

    @discord.ui.button(label="🏆 Word Record", style=discord.ButtonStyle.red)
    async def wordrecord(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = (
            "**Word record :**\n"
            "• 1 essai : 100 gemmes 💎\n"
            "• 2 essais : 170 gemmes 💎\n"
            "• 3 essais : 230 gemmes 💎"
        )
        await interaction.response.edit_message(content=desc, view=WordRecordBuyView())

    @discord.ui.button(label="✨ Rôle esthétique", style=discord.ButtonStyle.gray)
    async def role(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = (
            "**Rôle esthétique :**\n"
            "• Rôle @@Ww (1 semaine) : 20 gemmes 💎\n"
            "• Rôle @@Ww (1 mois) : 50 gemmes 💎\n"
            "• Rôle @@Ww (permanent) : 100 gemmes 💎\n"
            "• Rôle personnalisé (ex: @Timcool_27) : 200 gemmes 💎"
        )
        await interaction.response.edit_message(content=desc, view=RoleBuyView())

# ----- Views pour acheter les offres -----

class ShortsBuyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    async def process_purchase(self, interaction: discord.Interaction, nom, prix):
        user_id = str(interaction.user.id)
        gems = bot.user_gemmes.get(user_id, 0)
        if gems < prix:
            await interaction.response.send_message(f"❌ Tu n'as pas assez de gemmes pour **{nom}**.", ephemeral=True)
            return
        bot.user_gemmes[user_id] -= prix
        await update_gemmes_message()
        await interaction.response.send_message(f"✅ Tu as acheté **{nom}** pour {prix} gemmes.", ephemeral=True)
        # Ping créateur dans salon offres
        if bot.shop_channel_id:
            salon = bot.get_channel(bot.shop_channel_id)
            if salon:
                await salon.send(f"<@{CREATOR_ID}> : {interaction.user.mention} a acheté l'offre **{nom}** !")

    @discord.ui.button(label="1 clip : 80 💎", style=discord.ButtonStyle.green)
    async def buy1clip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_purchase(interaction, "1 clip edit short", 80)

    @discord.ui.button(label="2 clips : 110 💎", style=discord.ButtonStyle.green)
    async def buy2clips(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_purchase(interaction, "2 clips edit short", 110)

    @discord.ui.button(label="1 clip musique au choix : 90 💎", style=discord.ButtonStyle.green)
    async def buy1clipmusique(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_purchase(interaction, "1 clip musique au choix", 90)

    @discord.ui.button(label="2 clips musique au choix : 120 💎", style=discord.ButtonStyle.green)
    async def buy2clipsmusique(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_purchase(interaction, "2 clips musique au choix", 120)

class CacheBuyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    async def process_purchase(self, interaction: discord.Interaction, nom, prix):
        user_id = str(interaction.user.id)
        gems = bot.user_gemmes.get(user_id, 0)
        if gems < prix:
            await interaction.response.send_message(f"❌ Tu n'as pas assez de gemmes pour **{nom}**.", ephemeral=True)
            return
        bot.user_gemmes[user_id] -= prix
        await update_gemmes_message()
        await interaction.response.send_message(f"✅ Tu as acheté **{nom}** pour {prix} gemmes.", ephemeral=True)
        if bot.shop_channel_id:
            salon = bot.get_channel(bot.shop_channel_id)
            if salon:
                await salon.send(f"<@{CREATOR_ID}> : {interaction.user.mention} a acheté l'offre **{nom}** !")

    @discord.ui.button(label="4 manches : 150 💎", style=discord.ButtonStyle.green)
    async def buy4manches(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_purchase(interaction, "4 manches cache-cache", 150)

    @discord.ui.button(label="6 manches : 200 💎", style=discord.ButtonStyle.green)
    async def buy6manches(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_purchase(interaction, "6 manches cache-cache", 200)

    @discord.ui.button(label="8 manches : 250 💎", style=discord.ButtonStyle.green)
    async def buy8manches(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_purchase(interaction, "8 manches cache-cache", 250)

class WordRecordBuyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    async def process_purchase(self, interaction: discord.Interaction, nom, prix):
        user_id = str(interaction.user.id)
        gems = bot.user_gemmes.get(user_id, 0)
        if gems < prix:
            await interaction.response.send_message(f"❌ Tu n'as pas assez de gemmes pour **{nom}**.", ephemeral=True)
            return
        bot.user_gemmes[user_id] -= prix
        await update_gemmes_message()
        await interaction.response.send_message(f"✅ Tu as acheté **{nom}** pour {prix} gemmes.", ephemeral=True)
        if bot.shop_channel_id:
            salon = bot.get_channel(bot.shop_channel_id)
            if salon:
                await salon.send(f"<@{CREATOR_ID}> : {interaction.user.mention} a acheté l'offre **{nom}** !")

    @discord.ui.button(label="1 essai : 100 💎", style=discord.ButtonStyle.green)
    async def buy1essai(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_purchase(interaction, "1 essai word record", 100)

    @discord.ui.button(label="2 essais : 170 💎", style=discord.ButtonStyle.green)
    async def buy2essais(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_purchase(interaction, "2 essais word record", 170)

    @discord.ui.button(label="3 essais : 230 💎", style=discord.ButtonStyle.green)
    async def buy3essais(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_purchase(interaction, "3 essais word record", 230)

class RoleBuyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    async def process_role_purchase(self, interaction: discord.Interaction, role: discord.Role, prix: int, duration_seconds=None):
        user_id = str(interaction.user.id)
        gems = bot.user_gemmes.get(user_id, 0)
        if gems < prix:
            await interaction.response.send_message(f"❌ Tu n'as pas assez de gemmes pour ce rôle.", ephemeral=True)
            return

        # Check si rôle permanent déjà possédé
        if duration_seconds is None and role in interaction.user.roles:
            await interaction.response.send_message("❌ Tu as déjà ce rôle permanent.", ephemeral=True)
            return

        bot.user_gemmes[user_id] -= prix
        await update_gemmes_message()

        # Ajout du rôle
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ Rôle **{role.name}** ajouté pour {interaction.user.mention}.", ephemeral=True)

        # Ping créateur du serveur dans salon offres sauf pour rôles persos
        if bot.shop_channel_id and role.id in (ROLE_AWW_ID, ROLE_TIMCOOL_ID):
            salon = bot.get_channel(bot.shop_channel_id)
            if salon:
                # Mention du rôle en violet sans notification
                mention_aww = salon.guild.get_role(ROLE_AWW_ID).mention
                mention_tim = salon.guild.get_role(ROLE_TIMCOOL_ID).mention
                await salon.send(f"<@{CREATOR_ID}> : {interaction.user.mention} a acheté le rôle esthétique {mention_aww} ou {mention_tim}.")

        # Si durée, retire le rôle après
        if duration_seconds:
            await asyncio.sleep(duration_seconds)
            await interaction.user.remove_roles(role)
            # Pas besoin de notifier pour le retrait

    @discord.ui.button(label="Rôle @@Ww (1 semaine) - 20 💎", style=discord.ButtonStyle.green)
    async def role_1week(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(ROLE_AWW_ID)
        await self.process_role_purchase(interaction, role, 20, duration_seconds=7*24*3600)

    @discord.ui.button(label="Rôle @@Ww (1 mois) - 50 💎", style=discord.ButtonStyle.green)
    async def role_1month(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(ROLE_AWW_ID)
        await self.process_role_purchase(interaction, role, 50, duration_seconds=30*24*3600)

    @discord.ui.button(label="Rôle @@Ww (permanent) - 100 💎", style=discord.ButtonStyle.green)
    async def role_permanent(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(ROLE_AWW_ID)
        await self.process_role_purchase(interaction, role, 100)

    @discord.ui.button(label="Rôle personnalisé - 200 💎", style=discord.ButtonStyle.green)
    async def role_perso(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        gems = bot.user_gemmes.get(user_id, 0)
        prix = 200
        if gems < prix:
            await interaction.response.send_message("❌ Tu n'as pas assez de gemmes pour ce rôle personnalisé.", ephemeral=True)
            return
        bot.user_gemmes[user_id] -= prix
        await update_gemmes_message()

        # Créer rôle personnalisé au nom du membre
        guild = interaction.guild
        role_name = f"Perso {interaction.user.display_name}"
        # Vérifie si rôle existe déjà
        role = get(guild.roles, name=role_name)
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Rôle personnalisé {role_name} déjà existant, rôle ajouté.", ephemeral=True)
            return

        # Crée le rôle, couleur violet par exemple
        role = await guild.create_role(name=role_name, colour=discord.Colour.purple())
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ Rôle personnalisé **{role_name}** créé et ajouté.", ephemeral=True)

        # Pas besoin de notifier le créateur ni ping dans le salon offres

# ----- Commande shop -----

@bot.command()
async def shop(ctx):
    user_id = str(ctx.author.id)
    gems = bot.user_gemmes.get(user_id, 0)
    embed = discord.Embed(
        title="🛒 Boutique de gemmes",
        description=f"Tu as **{gems}** gemmes 💎\nChoisis une catégorie ci-dessous.",
        color=discord.Color.blue()
    )
    view = ShopView()
    await ctx.send(embed=embed, view=view)

# ----- Event on_ready -----
@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    # Si gemmes channel est défini mais pas message, crée le message
    if bot.gemmes_channel_id and not bot.gemmes_message_id:
        channel = bot.get_channel(bot.gemmes_channel_id)
        if channel:
            embed = discord.Embed(title="💎 Gemmes des membres", description="Chargement...", color=0x00ff00)
            msg = await channel.send(embed=embed)
            bot.gemmes_message_id = msg.id
            await update_gemmes_message()

# ----- Lancement du bot -----
bot.run(os.getenv("DISCORD_TOKEN"))
