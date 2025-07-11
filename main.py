import discord
from discord.ext import commands
from aiohttp import web
import asyncio
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="T.", intents=intents)

bot.user_gemmes = {}
bot.shop_channel_id = None
bot.gemmes_channel_id = None
bot.creator_id = 1089542697108377621  # ID du créateur du serveur (ping à chaque achat)
ROLE_WW_ID = 1386397029822890114  # Rôle @@Ww (pour mention "sans notification")
ROLE_PERSONNALISE_EXEMPLE_ID = 1371083702028865538  # Exemple role perso (pas utilisé directement)

# ----- Serveur web minimal pour Render -----
async def handle(request):
    return web.Response(text="Bot en ligne !")

async def run_webserver():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# ----- Fonction pour afficher ou mettre à jour le message des gemmes -----
async def update_gemmes_message():
    if bot.gemmes_channel_id is None:
        return
    channel = bot.get_channel(bot.gemmes_channel_id)
    if channel is None:
        return

    lines = ["**Liste des gemmes des membres :**"]
    for user_id, gemmes in bot.user_gemmes.items():
        member = channel.guild.get_member(int(user_id))
        if member:
            lines.append(f"- {member.display_name} : {gemmes} 💎")
    content = "\n".join(lines)

    # On récupère le dernier message du bot dans le salon pour éditer
    async for message in channel.history(limit=50):
        if message.author == bot.user:
            await message.edit(content=content)
            return
    # Si pas trouvé, on envoie un nouveau message
    await channel.send(content)

# ----- Vérification que l’auteur est le créateur du serveur -----
def is_owner(ctx):
    return ctx.author.id == ctx.guild.owner_id

# ----- Commandes -----

@bot.command()
async def addgemmes(ctx, membre: discord.Member, montant: int):
    if not is_owner(ctx):
        return await ctx.send("❌ Seul le créateur du serveur peut utiliser cette commande.")
    user_id = str(membre.id)
    bot.user_gemmes[user_id] = bot.user_gemmes.get(user_id, 0) + montant
    await ctx.send(f"✅ {montant} gemmes ont été ajoutées à {membre.mention}.")
    await update_gemmes_message()

@bot.command()
async def deletegemmes(ctx, membre: discord.Member, montant: int):
    if not is_owner(ctx):
        return await ctx.send("❌ Seul le créateur du serveur peut utiliser cette commande.")
    user_id = str(membre.id)
    bot.user_gemmes[user_id] = max(bot.user_gemmes.get(user_id, 0) - montant, 0)
    await ctx.send(f"✅ {montant} gemmes ont été retirées à {membre.mention}.")
    await update_gemmes_message()

@bot.command(name="set_salon_offres")
async def set_salon_offres(ctx, salon: discord.TextChannel):
    if not is_owner(ctx):
        return await ctx.send("❌ Seul le créateur du serveur peut utiliser cette commande.")
    bot.shop_channel_id = salon.id
    await ctx.send(f"✅ Salon des offres défini : {salon.mention}")

@bot.command(name="set_salon_gemmes")
async def set_salon_gemmes(ctx, salon: discord.TextChannel):
    if not is_owner(ctx):
        return await ctx.send("❌ Seul le créateur du serveur peut utiliser cette commande.")
    bot.gemmes_channel_id = salon.id
    await ctx.send(f"✅ Salon des gemmes défini : {salon.mention}")
    await update_gemmes_message()

# ----- Shop avec catégories et achats -----

class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎬 Edits Shorts", style=discord.ButtonStyle.blurple)
    async def shorts(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Edit pour des shorts", description=(
            "• 1 clip : 80 gemmes 💎\n"
            "• 2 clips : 110 gemmes 💎\n"
            "• 1 clip (musique au choix) : 90 gemmes 💎\n"
            "• 2 clips (musique au choix) : 120 gemmes 💎"
        ))
        await interaction.response.edit_message(embed=embed, view=BuyView("shorts"))

    @discord.ui.button(label="🎮 Cache-Cache", style=discord.ButtonStyle.green)
    async def cache(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Vidéo cache-cache avec moi", description=(
            "• 4 manches : 150 gemmes 💎\n"
            "• 6 manches : 200 gemmes 💎\n"
            "• 8 manches : 250 gemmes 💎"
        ))
        await interaction.response.edit_message(embed=embed, view=BuyView("cache"))

    @discord.ui.button(label="🏆 Word Record", style=discord.ButtonStyle.red)
    async def wordrecord(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Word record", description=(
            "• 1 essai : 100 gemmes 💎\n"
            "• 2 essais : 170 gemmes 💎\n"
            "• 3 essais : 230 gemmes 💎"
        ))
        await interaction.response.edit_message(embed=embed, view=BuyView("wordrecord"))

    @discord.ui.button(label="✨ Rôle esthétique", style=discord.ButtonStyle.gray)
    async def role(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Rôle esthétique", description=(
            "• Rôle @@Ww (1 semaine) : 20 gemmes 💎\n"
            "• Rôle @@Ww (1 mois) : 50 gemmes 💎\n"
            "• Rôle @@Ww (permanent) : 100 gemmes 💎\n"
            "• Rôle personnalisé (ex: @Timcool_27) : 200 gemmes 💎"
        ))
        await interaction.response.edit_message(embed=embed, view=BuyView("role"))

class BuyView(discord.ui.View):
    def __init__(self, category):
        super().__init__(timeout=None)
        self.category = category
        self.prices = {
            "shorts": {
                "1 clip": 80,
                "2 clips": 110,
                "1 clip (musique au choix)": 90,
                "2 clips (musique au choix)": 120,
            },
            "cache": {
                "4 manches": 150,
                "6 manches": 200,
                "8 manches": 250,
            },
            "wordrecord": {
                "1 essai": 100,
                "2 essais": 170,
                "3 essais": 230,
            },
            "role": {
                "Rôle @@Ww (1 semaine)": 20,
                "Rôle @@Ww (1 mois)": 50,
                "Rôle @@Ww (permanent)": 100,
                "Rôle personnalisé": 200,
            }
        }
        # Crée un bouton par offre
        for offer_name in self.prices[category]:
            self.add_item(BuyButton(offer_name, self.prices[category][offer_name], category))

class BuyButton(discord.ui.Button):
    def __init__(self, label, price, category):
        super().__init__(label=label, style=discord.ButtonStyle.green)
        self.price = price
        self.category = category

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        gemmes = bot.user_gemmes.get(user_id, 0)
        if gemmes < self.price:
            await interaction.response.send_message(f"❌ Tu n'as pas assez de gemmes ({gemmes}) pour acheter cette offre (coût : {self.price})", ephemeral=True)
            return

        # Déduire les gemmes
        bot.user_gemmes[user_id] = gemmes - self.price
        await update_gemmes_message()

        guild = interaction.guild
        member = interaction.user

        # Selon la catégorie, on gère différemment
        if self.category == "role":
            if self.label == "Rôle personnalisé":
                # Créer un rôle personnalisé au nom du membre
                role_name = str(member)
                existing_role = discord.utils.get(guild.roles, name=role_name)
                if existing_role:
                    await interaction.response.send_message("❌ Tu as déjà un rôle personnalisé.", ephemeral=True)
                    return
                new_role = await guild.create_role(name=role_name, colour=discord.Colour.purple())
                await member.add_roles(new_role)

                # Pas de notification, pas besoin de ping
                await interaction.response.send_message(f"✅ Rôle personnalisé créé et ajouté : {new_role.mention}", ephemeral=True)

            else:
                # Rôles @@Ww temporaires selon durée
                role_ww = guild.get_role(ROLE_WW_ID)
                if role_ww is None:
                    await interaction.response.send_message("❌ Le rôle @@Ww n'existe pas sur ce serveur.", ephemeral=True)
                    return

                # Durée selon le label
                durée = None
                if "1 semaine" in self.label:
                    durée = 7 * 24 * 3600
                elif "1 mois" in self.label:
                    durée = 30 * 24 * 3600
                elif "permanent" in self.label:
                    durée = None

                # Vérifier si membre a déjà ce rôle permanent
                if durée is None and role_ww in member.roles:
                    await interaction.response.send_message("❌ Tu as déjà ce rôle permanent.", ephemeral=True)
                    return

                # Ajout du rôle
                await member.add_roles(role_ww)
                await interaction.response.send_message(f"✅ Rôle {role_ww.mention} ajouté.", ephemeral=True)

                # Notifier dans salon offres + ping créateur du serv, mention rôle sans notif
                if bot.shop_channel_id:
                    salon_offres = bot.get_channel(bot.shop_channel_id)
                    if salon_offres:
                        # Mention du rôle sans ping réel avec format <@&id> et désactivé les mentions
                        await salon_offres.send(
                            f"{member.mention} a acheté **{self.label}** pour {self.price} gemmes. "
                            f"<@&{ROLE_WW_ID}> {bot.get_user(bot.creator_id).mention}"
                        )

                # Si durée temporaire, retirer après délai
                if durée is not None:
                    async def retirer_role():
                        await asyncio.sleep(durée)
                        await member.remove_roles(role_ww)

                    bot.loop.create_task(retirer_role())

        else:
            # Offres non rôles, on notifie dans salon offres et ping créateur du serv
            if bot.shop_channel_id:
                salon_offres = bot.get_channel(bot.shop_channel_id)
                if salon_offres:
                    await salon_offres.send(
                        f"{member.mention} a acheté **{self.label}** pour {self.price} gemmes. "
                        f"{bot.get_user(bot.creator_id).mention}"
                    )

            await interaction.response.send_message(f"✅ Offre achetée : {self.label}", ephemeral=True)

# ----- Commande shop -----

@bot.command()
async def shop(ctx):
    user_id = str(ctx.author.id)
    gemmes = bot.user_gemmes.get(user_id, 0)
    embed = discord.Embed(title="Boutique", description=f"Tu as {gemmes} gemmes 💎. Choisis une catégorie ci-dessous.")
    await ctx.send(embed=embed, view=ShopView())

# ----- Events -----

@bot.event
async def on_ready():
    print(f"Bot prêt : {bot.user} (ID: {bot.user.id})")

# ----- Lancement bot + serveur web Render -----

async def main():
    await run_webserver()
    await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())
