import discord
from discord.ext import commands
from aiohttp import web
import asyncio
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="T.", intents=intents)

# IDs fixes pour ping roles
ROLE_WW_ID = 1386397029822890114  # rôle @@Ww
CREATOR_ID = 1089542697108377621  # créateur serveur (ping à chaque achat)

bot.user_gemmes = {}
bot.shop_channel_id = None       # salon pour notifier achats
bot.gemmes_channel_id = None     # salon pour afficher gemmes
bot.gemmes_message_id = None     # ID du message affichant les gemmes

# --- Serveur web pour Render ---
async def handle(request):
    return web.Response(text="Bot en ligne !")

async def run_webserver():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- Fonction pour mettre à jour message des gemmes ---
async def update_gemmes_message():
    if not bot.gemmes_channel_id or not bot.gemmes_message_id:
        return
    channel = bot.get_channel(bot.gemmes_channel_id)
    if not channel:
        return
    try:
        message = await channel.fetch_message(bot.gemmes_message_id)
    except:
        return

    if not bot.user_gemmes:
        content = "Aucun membre avec des gemmes pour le moment."
    else:
        lines = []
        for user_id, gems in bot.user_gemmes.items():
            member = channel.guild.get_member(int(user_id))
            name = member.display_name if member else f"ID:{user_id}"
            lines.append(f"**{name}** : {gems} 💎")
        content = "**Gemmes des membres :**\n" + "\n".join(lines)
    await message.edit(content=content)

# --- Vérification : commande réservée au créateur serveur ---
def is_guild_owner():
    async def predicate(ctx):
        return ctx.author.id == ctx.guild.owner_id
    return commands.check(predicate)

# --- Commandes ---

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
    new = max(current - montant, 0)
    bot.user_gemmes[user_id] = new
    await ctx.send(f"✅ {montant} gemmes ont été retirées à {membre.mention}.")
    await update_gemmes_message()

@bot.command(name="set_salon_offres")
@is_guild_owner()
async def set_salon_offres(ctx, salon: discord.TextChannel):
    bot.shop_channel_id = salon.id
    await ctx.send(f"✅ Salon des offres défini : {salon.mention}")

@bot.command(name="set_salon_gemmes")
@is_guild_owner()
async def set_salon_gemmes(ctx, salon: discord.TextChannel):
    bot.gemmes_channel_id = salon.id
    # On envoie le message affichant les gemmes pour la première fois
    message = await salon.send("Chargement des gemmes...")
    bot.gemmes_message_id = message.id
    await update_gemmes_message()
    await ctx.send(f"✅ Salon d'affichage des gemmes défini : {salon.mention}")

# --- Shop ---

class BuyButton(discord.ui.Button):
    def __init__(self, label, price, category):
        super().__init__(label=f"{label} ({price}💎)", style=discord.ButtonStyle.primary)
        self.label_base = label
        self.price = price
        self.category = category  # "role" ou "other"

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        gemmes = bot.user_gemmes.get(user_id, 0)
        member = interaction.user
        guild = interaction.guild

        if gemmes < self.price:
            await interaction.response.send_message(
                f"❌ Tu n'as pas assez de gemmes ({gemmes}) pour acheter cette offre (coût : {self.price})",
                ephemeral=True
            )
            return

        # Deduct gems
        bot.user_gemmes[user_id] = gemmes - self.price
        await update_gemmes_message()

        # Répondre d'abord à l'interaction
        await interaction.response.send_message(f"✅ Offre achetée : {self.label_base}", ephemeral=True)

        # Actions selon catégorie
        if self.category == "role":
            # Rôles @@Ww
            if self.label_base.startswith("Rôle @@Ww"):
                role_ww = guild.get_role(ROLE_WW_ID)
                if not role_ww:
                    await interaction.followup.send("❌ Le rôle @@Ww n'existe pas sur ce serveur.", ephemeral=True)
                    return

                # Check si déjà ce rôle
                if role_ww in member.roles:
                    await interaction.followup.send("❌ Tu as déjà ce rôle.", ephemeral=True)
                    return

                await member.add_roles(role_ww)
                dur = None
                if "1 semaine" in self.label_base:
                    dur = 7 * 24 * 3600
                elif "1 mois" in self.label_base:
                    dur = 30 * 24 * 3600
                elif "permanent" in self.label_base:
                    dur = None

                if dur:
                    async def remove_role_later():
                        await asyncio.sleep(dur)
                        try:
                            await member.remove_roles(role_ww)
                        except:
                            pass
                    bot.loop.create_task(remove_role_later())

            elif self.label_base == "Rôle personnalisé":
                # Créer rôle personnalisé au nom du membre
                role_name = str(member)
                existing_role = discord.utils.get(guild.roles, name=role_name)
                if existing_role:
                    await interaction.followup.send("❌ Tu as déjà un rôle personnalisé.", ephemeral=True)
                    return
                new_role = await guild.create_role(name=role_name, colour=discord.Colour.purple())
                await member.add_roles(new_role)
                # Pas de notif dans salon offres

        else:
            # Autres offres : ping créateur serveur dans salon offres
            if bot.shop_channel_id:
                salon_offres = bot.get_channel(bot.shop_channel_id)
                creator_user = bot.get_user(CREATOR_ID)
                if salon_offres and creator_user:
                    # Mention role @@Ww sans notification (mention role + suppress_notifications)
                    role_ww = guild.get_role(ROLE_WW_ID)
                    role_mention = role_ww.mention if role_ww else "@@@Ww"
                    # Envoyer message
                    await salon_offres.send(
                        f"{member.mention} a acheté **{self.label_base}** pour {self.price} gemmes. {creator_user.mention} {role_mention}",
                        allowed_mentions=discord.AllowedMentions(users=True, roles=False)
                    )

class ShopView(discord.ui.View):
    def __init__(self, category):
        super().__init__(timeout=None)
        self.category = category
        self.add_offers_buttons()

    def add_offers_buttons(self):
        # Selon la catégorie, on ajoute les boutons d'achat
        if self.category == "Edits Shorts":
            offers = [
                ("1 clip", 80),
                ("2 clips", 110),
                ("1 clip (musique au choix)", 90),
                ("2 clips (musique au choix)", 120),
            ]
        elif self.category == "Cache-Cache":
            offers = [
                ("4 manches", 150),
                ("6 manches", 200),
                ("8 manches", 250),
            ]
        elif self.category == "Word Record":
            offers = [
                ("1 essai", 100),
                ("2 essais", 170),
                ("3 essais", 230),
            ]
        elif self.category == "Rôle esthétique":
            offers = [
                ("Rôle @@Ww (1 semaine)", 20),
                ("Rôle @@Ww (1 mois)", 50),
                ("Rôle @@Ww (permanent)", 100),
                ("Rôle personnalisé", 200),
            ]
        else:
            offers = []

        for label, price in offers:
            category = "role" if "Rôle" in label else "other"
            self.add_item(BuyButton(label, price, category))

class CategorySelect(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CategoryDropdown())

class CategoryDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Edits Shorts", description="Voir les offres Edits Shorts"),
            discord.SelectOption(label="Cache-Cache", description="Voir les offres Cache-Cache"),
            discord.SelectOption(label="Word Record", description="Voir les offres Word Record"),
            discord.SelectOption(label="Rôle esthétique", description="Voir les rôles esthétiques"),
        ]
        super().__init__(placeholder="Choisis une catégorie...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        view = ShopView(category)
        # On met à jour le message avec les boutons et le titre
        content = f"**Boutique - {category}**\n\nClique sur un bouton pour acheter une offre.\n" \
                  f"Tu as {bot.user_gemmes.get(str(interaction.user.id), 0)} gemmes."
        await interaction.response.edit_message(content=content, view=view)

@bot.command()
async def shop(ctx):
    gemmes = bot.user_gemmes.get(str(ctx.author.id), 0)
    content = f"**Boutique**\n\nTu as {gemmes} gemmes.\nChoisis une catégorie ci-dessous :"
    view = CategorySelect()
    await ctx.send(content, view=view)

# --- Event on_ready ---

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user} (ID : {bot.user.id})")
    # Démarrer serveur web (Render)
    bot.loop.create_task(run_webserver())

# --- Lancement du bot ---
bot.run(os.environ.get("TOKEN"))
