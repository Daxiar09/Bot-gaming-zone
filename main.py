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
bot.gemmes_message_id = None

# — Serveur HTTP pour Render
async def handle(request):
    return web.Response(text="Bot en ligne !")

async def run_webserver():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# — Met à jour le message des gemmes
async def update_gemmes_message():
    if not bot.gemmes_channel_id or not bot.gemmes_message_id:
        return
    channel = bot.get_channel(bot.gemmes_channel_id)
    if not channel:
        return
    try:
        msg = await channel.fetch_message(bot.gemmes_message_id)
    except discord.NotFound:
        return
    lines = ["**💎 Gemmes des membres :**"]
    for uid, count in bot.user_gemmes.items():
        lines.append(f"<@{uid}> : {count} gemmes 💎")
    await msg.edit(content="\n".join(lines))

@bot.event
async def on_ready():
    print(f"{bot.user} est prêt !")

# — Vérifie si auteur est créateur du serveur
def is_owner(ctx):
    return ctx.author.id == ctx.guild.owner_id

# — Commandes réservées

@bot.command()
async def addgemmes(ctx, membre: discord.Member, montant: int):
    if not is_owner(ctx):
        return await ctx.send("❌ Seul le créateur du serveur peut utiliser cette commande.")
    uid = str(membre.id)
    bot.user_gemmes[uid] = bot.user_gemmes.get(uid, 0) + montant
    await ctx.send(f"✅ {montant} gemmes ajoutées à {membre.mention}.")
    await update_gemmes_message()

@bot.command()
async def deletegemmes(ctx, membre: discord.Member, montant: int):
    if not is_owner(ctx):
        return await ctx.send("❌ Seul le créateur du serveur peut utiliser cette commande.")
    uid = str(membre.id)
    bot.user_gemmes[uid] = max(bot.user_gemmes.get(uid, 0) - montant, 0)
    await ctx.send(f"🗑️ {montant} gemmes retirées à {membre.mention}.")
    await update_gemmes_message()

@bot.command()
async def set_salon_gemmes(ctx, salon: discord.TextChannel):
    if not is_owner(ctx):
        return await ctx.send("❌ Seul le créateur du serveur peut utiliser cette commande.")
    bot.gemmes_channel_id = salon.id
    msg = await salon.send("**💎 Gemmes des membres :**\n_Aucune donnée._")
    bot.gemmes_message_id = msg.id
    await ctx.send(f"✅ Salon d'affichage des gemmes défini : {salon.mention}")
    await update_gemmes_message()

@bot.command()
async def set_salon_offres(ctx, salon: discord.TextChannel):
    if not is_owner(ctx):
        return await ctx.send("❌ Seul le créateur du serveur peut utiliser cette commande.")
    bot.shop_channel_id = salon.id
    await ctx.send(f"✅ Salon des offres défini : {salon.mention}")

# — Boutique accessible à tous

class OfferButton(discord.ui.Button):
    def __init__(self, label, price, offer_type, duration=None, role_id=None):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.price = price
        self.offer_type = offer_type
        self.duration = duration
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        if bot.user_gemmes.get(uid, 0) < self.price:
            return await interaction.response.send_message("❌ Tu n’as pas assez de gemmes.", ephemeral=True)
        bot.user_gemmes[uid] -= self.price
        await update_gemmes_message()

        if self.offer_type == "role":
            role = interaction.guild.get_role(self.role_id)
            if role:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"✅ Tu as reçu le rôle {role.mention} !", ephemeral=True)
                await asyncio.sleep(self.duration)
                await interaction.user.remove_roles(role)
        else:
            if bot.shop_channel_id:
                salon = bot.get_channel(bot.shop_channel_id)
                await salon.send(f"📦 {interaction.user.mention} a acheté `{self.label}`.")
            await interaction.response.send_message("✅ Achat effectué !", ephemeral=True)

class OfferView(discord.ui.View):
    def __init__(self, offers):
        super().__init__(timeout=None)
        for o in offers:
            self.add_item(OfferButton(**o))

class ShopView(discord.ui.View):
    @discord.ui.button(label="🎬 Edits Shorts", style=discord.ButtonStyle.blurple)
    async def shorts(self, interaction, button):
        offers = [
            {"label": "1 clip", "price": 80, "offer_type": "notif"},
            {"label": "2 clips", "price": 110, "offer_type": "notif"},
            {"label": "1 clip + musique", "price": 90, "offer_type": "notif"},
            {"label": "2 clips + musique", "price": 120, "offer_type": "notif"},
        ]
        await interaction.response.send_message("Choisis ton offre :", view=OfferView(offers), ephemeral=True)

    @discord.ui.button(label="🎮 Cache‑Cache", style=discord.ButtonStyle.green)
    async def cache(self, interaction, button):
        offers = [
            {"label": "4 manches", "price": 150, "offer_type": "notif"},
            {"label": "6 manches", "price": 200, "offer_type": "notif"},
            {"label": "8 manches", "price": 250, "offer_type": "notif"},
        ]
        await interaction.response.send_message("Choisis ton offre :", view=OfferView(offers), ephemeral=True)

    @discord.ui.button(label="🏆 World Record", style=discord.ButtonStyle.red)
    async def wordrecord(self, interaction, button):
        offers = [
            {"label": "1 essai", "price": 100, "offer_type": "notif"},
            {"label": "2 essais", "price": 170, "offer_type": "notif"},
            {"label": "3 essais", "price": 230, "offer_type": "notif"},
        ]
        await interaction.response.send_message("Choisis ton offre :", view=OfferView(offers), ephemeral=True)

    @discord.ui.button(label="✨ Rôle esthétique", style=discord.ButtonStyle.gray)
    async def role(self, interaction, button):
        offers = [
            {"label": "Rôle 1 semaine", "price": 20, "offer_type": "role", "duration": 7*24*3600, "role_id": 123456789012345678},
            {"label": "Rôle 1 mois", "price": 50, "offer_type": "role", "duration": 30*24*3600, "role_id": 123456789012345678},
            {"label": "Rôle permanent", "price": 100, "offer_type": "role", "duration": 10**8, "role_id": 123456789012345678},
        ]
        await interaction.response.send_message("Choisis ton rôle :", view=OfferView(offers), ephemeral=True)

@bot.command()
async def shop(ctx):
    await ctx.send("Voici la boutique :", view=ShopView())

# — Démarrage principal
async def main():
    await run_webserver()
    await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())
