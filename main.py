import discord
from discord.ext import commands, tasks
from aiohttp import web
import asyncio
import os

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="T.", intents=intents)

bot.user_gemmes = {}
bot.shop_channel_id = None  # salon où on notifie les achats (offres hors rôles persos)
bot.gemmes_channel_id = None  # salon où on affiche le message gemmes
bot.gemmes_message_id = None  # id du message affichant les gemmes

# IDs des rôles à mentionner muet
ROLE_WW_ID = 1386397029822890114
EXEMPLE_ROLE_PERSO_ID = 1371083702028865538

# Serveur web minimal pour Render
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

def is_owner():
    async def predicate(ctx):
        return ctx.author.id == ctx.guild.owner_id
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f"{bot.user} est prêt !")
    update_gemmes_message.start()

# Mise à jour automatique du message gemmes toutes les 30 secondes (ou selon besoin)
@tasks.loop(seconds=30)
async def update_gemmes_message():
    if bot.gemmes_channel_id is None or bot.gemmes_message_id is None:
        return
    channel = bot.get_channel(bot.gemmes_channel_id)
    if channel is None:
        return
    try:
        message = await channel.fetch_message(bot.gemmes_message_id)
    except:
        return
    embed = discord.Embed(title="Gemmes des membres", color=discord.Color.gold())
    if not bot.user_gemmes:
        embed.description = "Aucun membre n'a de gemmes pour le moment."
    else:
        desc = ""
        for user_id, gems in bot.user_gemmes.items():
            member = channel.guild.get_member(int(user_id))
            if member:
                desc += f"{member.display_name} : **{gems}** 💎\n"
        embed.description = desc
    await message.edit(embed=embed)

# Commandes accessibles uniquement au créateur du serveur
@bot.command()
@is_owner()
async def addgemmes(ctx, membre: discord.Member, montant: int):
    user_id = str(membre.id)
    bot.user_gemmes[user_id] = bot.user_gemmes.get(user_id, 0) + montant
    await ctx.send(f"✅ {montant} gemmes ont été ajoutées à {membre.mention}.")

@bot.command()
@is_owner()
async def deletegemmes(ctx, membre: discord.Member, montant: int):
    user_id = str(membre.id)
    current = bot.user_gemmes.get(user_id, 0)
    new_amount = max(current - montant, 0)
    bot.user_gemmes[user_id] = new_amount
    await ctx.send(f"✅ {montant} gemmes ont été retirées de {membre.mention}.")

@bot.command(name="set_salon_offres")
@is_owner()
async def set_salon_offres(ctx, salon: discord.TextChannel):
    bot.shop_channel_id = salon.id
    await ctx.send(f"✅ Salon offres défini sur {salon.mention}.")

@bot.command(name="set_salon_gemmes")
@is_owner()
async def set_salon_gemmes(ctx, salon: discord.TextChannel):
    bot.gemmes_channel_id = salon.id
    # Envoie un message initial ou récupère l'existant
    messages = await salon.history(limit=50).flatten()
    for msg in messages:
        if msg.author == bot.user and msg.embeds:
            # On suppose que c'est le message gemmes si trouvé
            bot.gemmes_message_id = msg.id
            await ctx.send(f"✅ Message gemmes existant trouvé et défini.")
            return
    # Sinon envoie un nouveau message
    embed = discord.Embed(title="Gemmes des membres", description="Aucun membre n'a de gemmes pour le moment.", color=discord.Color.gold())
    message = await salon.send(embed=embed)
    bot.gemmes_message_id = message.id
    await ctx.send(f"✅ Salon gemmes défini et message initial envoyé.")

class ShopView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=None)
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Seul l'auteur de la commande peut interagir avec les boutons
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Ce n'est pas votre boutique.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🎬 Edits Shorts", style=discord.ButtonStyle.blurple)
    async def shorts(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Offres Edits Shorts", color=discord.Color.blurple())
        embed.description = (
            "• 1 clip : 80 gemmes 💎\n"
            "• 2 clips : 110 gemmes 💎\n"
            "• 1 clip (musique au choix) : 90 gemmes 💎\n"
            "• 2 clips (musique au choix) : 120 gemmes 💎"
        )
        await interaction.response.edit_message(embed=embed, view=BuyView(self.author, "edits"))

    @discord.ui.button(label="🎮 Cache-Cache", style=discord.ButtonStyle.green)
    async def cache(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Offres Vidéo Cache-Cache", color=discord.Color.green())
        embed.description = (
            "• 4 manches : 150 gemmes 💎\n"
            "• 6 manches : 200 gemmes 💎\n"
            "• 8 manches : 250 gemmes 💎"
        )
        await interaction.response.edit_message(embed=embed, view=BuyView(self.author, "cachecache"))

    @discord.ui.button(label="🏆 Word Record", style=discord.ButtonStyle.red)
    async def wordrecord(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Offres Word Record", color=discord.Color.red())
        embed.description = (
            "• 1 essai : 100 gemmes 💎\n"
            "• 2 essais : 170 gemmes 💎\n"
            "• 3 essais : 230 gemmes 💎"
        )
        await interaction.response.edit_message(embed=embed, view=BuyView(self.author, "wordrecord"))

    @discord.ui.button(label="✨ Rôle esthétique", style=discord.ButtonStyle.gray)
    async def role(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Offres Rôles Esthétiques", color=discord.Color.greyple())
        embed.description = (
            "• Rôle @@Ww (1 semaine) : 20 gemmes 💎\n"
            "• Rôle @@Ww (1 mois) : 50 gemmes 💎\n"
            "• Rôle @@Ww (permanent) : 100 gemmes 💎\n"
            "• Rôle personnalisé (ex: @Timcool_27) : 200 gemmes 💎"
        )
        await interaction.response.edit_message(embed=embed, view=BuyView(self.author, "role"))

class BuyView(discord.ui.View):
    def __init__(self, author, category):
        super().__init__(timeout=None)
        self.author = author
        self.category = category

        # Offres par catégorie : (nom, prix, durée en secondes, rôle_id (None si pas rôle))
        self.offers = {
            "edits": [
                ("1 clip", 80, None, None),
                ("2 clips", 110, None, None),
                ("1 clip (musique au choix)", 90, None, None),
                ("2 clips (musique au choix)", 120, None, None),
            ],
            "cachecache": [
                ("4 manches", 150, None, None),
                ("6 manches", 200, None, None),
                ("8 manches", 250, None, None),
            ],
            "wordrecord": [
                ("1 essai", 100, None, None),
                ("2 essais", 170, None, None),
                ("3 essais", 230, None, None),
            ],
            "role": [
                ("Rôle @@Ww (1 semaine)", 20, 7*24*3600, ROLE_WW_ID),
                ("Rôle @@Ww (1 mois)", 50, 30*24*3600, ROLE_WW_ID),
                ("Rôle @@Ww (permanent)", 100, None, ROLE_WW_ID),
                ("Rôle personnalisé", 200, None, EXEMPLE_ROLE_PERSO_ID),
            ]
        }

        # Ajout des boutons selon la catégorie
        for i, (name, price, duration, role_id) in enumerate(self.offers.get(category, [])):
            button = discord.ui.Button(label=f"{name} - {price}💎", style=discord.ButtonStyle.primary, custom_id=f"buy_{category}_{i}")
            button.callback = self.buy_callback
            self.add_item(button)

    async def buy_callback(self, interaction: discord.Interaction):
        custom_id = interaction.data["custom_id"]
        # Ex: buy_edits_0
        parts = custom_id.split("_")
        category = parts[1]
        index = int(parts[2])
        user_id = str(interaction.user.id)
        offers = self.offers.get(category, [])
        if index >= len(offers):
            await interaction.response.send_message("Offre invalide.", ephemeral=True)
            return
        name, price, duration, role_id = offers[index]

        # Vérifier gemmes
        user_gems = bot.user_gemmes.get(user_id, 0)
        if user_gems < price:
            await interaction.response.send_message(f"❌ Vous n'avez pas assez de gemmes ({user_gems} < {price}).", ephemeral=True)
            return

        # Déduire les gemmes
        bot.user_gemmes[user_id] = user_gems - price

        # Traitement selon type d'offre
        guild = interaction.guild
        member = interaction.user

        if category == "role":
            if name == "Rôle personnalisé":
                # Créer un rôle perso nommé d'après le membre (ex: Timcool_27)
                role_name = str(member)
                role = await guild.create_role(name=role_name, color=discord.Color.purple(), mentionable=False)
                await member.add_roles(role, reason="Achat rôle personnalisé boutique")
                # Pas de notif dans le salon offres
                await interaction.response.send_message(f"✅ Rôle personnalisé créé et ajouté : {role.name}", ephemeral=True)
            else:
                # Rôle standard @@Ww
                role = guild.get_role(role_id)
                if role in member.roles:
                    await interaction.response.send_message("❌ Vous avez déjà ce rôle.", ephemeral=True)
                    return
                await member.add_roles(role, reason="Achat rôle boutique")
                await interaction.response.send_message(f"✅ Rôle {role.name} ajouté.", ephemeral=True)
                if duration is not None:
                    # Retirer le rôle après duration
                    async def remove_role_later():
                        await asyncio.sleep(duration)
                        try:
                            await member.remove_roles(role, reason="Fin durée rôle boutique")
                        except:
                            pass
                    bot.loop.create_task(remove_role_later())
                # Ping muet dans le salon offres
                if bot.shop_channel_id:
                    salon = guild.get_channel(bot.shop_channel_id)
                    if salon:
                        # Mention muette (pas de notif)
                        mention = f"<@&{ROLE_WW_ID}>"
                        await salon.send(f"{mention} {member.mention} a acheté {name} pour {price} gemmes.")
        else:
            # Offre standard, pas un rôle, on ping le créateur dans salon offres
            if bot.shop_channel_id:
                salon = guild.get_channel(bot.shop_channel_id)
                if salon:
                    mention = f"<@&{ROLE_WW_ID}>"
                    await salon.send(f"{mention} {member.mention} a acheté {name} pour {price} gemmes.")
            await interaction.response.send_message(f"✅ Achat validé : {name}", ephemeral=True)

        # Mise à jour message gemmes
        await update_gemmes_message()

@bot.command()
async def shop(ctx):
    user_id = str(ctx.author.id)
    gems = bot.user_gemmes.get(user_id, 0)
    embed = discord.Embed(
        title="Boutique des gemmes",
        description=f"Vous avez actuellement **{gems}** gemmes 💎.\nChoisissez une catégorie ci-dessous :",
        color=discord.Color.gold()
    )
    view = ShopView(ctx.author)
    await ctx.send(embed=embed, view=view)

async def main():
    await run_webserver()
    await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())
