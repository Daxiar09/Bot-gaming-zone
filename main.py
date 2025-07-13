import json
import discord
from discord.ext import commands, tasks
from aiohttp import web
import asyncio
import os

DATA_FILE = "data.json"


def save_data():
    data = {
        "gemmes": bot.user_gemmes,
        "salon_offres_id": bot.shop_channel_id,
        "salon_gemmes_id": bot.gemmes_channel_id,
        "message_gemmes_id": bot.gemmes_message_id
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            bot.user_gemmes = data.get("gemmes", {})
            bot.shop_channel_id = data.get("salon_offres_id")
            bot.gemmes_channel_id = data.get("salon_gemmes_id")
            bot.gemmes_message_id = data.get("message_gemmes_id")


intents = discord.Intents.all()
bot = commands.Bot(command_prefix="T.", intents=intents)

bot.user_gemmes = {}
bot.shop_channel_id = None
bot.gemmes_channel_id = None
bot.gemmes_message_id = None

OWNER_ID = 1089542697108377621
ROLE_WW_ID = 1386397029822890114


# ───── Web server ─────
async def handle(request):
    return web.Response(text="Bot en ligne !")


async def run_webserver():
    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


# ───── Mise à jour message gemmes ─────
async def update_gemmes_message():
    if bot.gemmes_channel_id and bot.gemmes_message_id:
        channel = bot.get_channel(bot.gemmes_channel_id)
        try:
            message = await channel.fetch_message(bot.gemmes_message_id)
        except:
            return
        content = "**💎 Gemmes des membres :**\n"
        for user_id, gemmes in bot.user_gemmes.items():
            user = await bot.fetch_user(int(user_id))
            content += f"{user.mention} → {gemmes} gemmes\n"
        await message.edit(content=content)


# ───── Événements ─────
@bot.event
async def on_ready():
    load_data()
    print(f"{bot.user} est prêt !")


# ───── Commandes Owner ─────
def is_owner(ctx):
    return ctx.author.id == OWNER_ID


@bot.command()
async def addgemmes(ctx, membre: discord.Member, montant: int):
    if not is_owner(ctx):
        return await ctx.send(
            "❌ TU n,es pas autorisé à utiliser cette commande.")
    uid = str(membre.id)
    bot.user_gemmes[uid] = bot.user_gemmes.get(uid, 0) + montant
    await ctx.send(f"✅ {montant} gemmes ajoutées à {membre.mention}")
    await update_gemmes_message()
    save_data()


@bot.command()
async def deletegemmes(ctx, membre: discord.Member, montant: int):
    if not is_owner(ctx):
        return await ctx.send(
            "❌ Seul le créateur peut utiliser cette commande.")
    uid = str(membre.id)
    bot.user_gemmes[uid] = max(0, bot.user_gemmes.get(uid, 0) - montant)
    await ctx.send(f"❌ {montant} gemmes retirées à {membre.mention}")
    await update_gemmes_message()
    save_data()


@bot.command()
async def set_salon_offres(ctx, salon: discord.TextChannel):
    if not is_owner(ctx):
        return await ctx.send(
            "❌ Seul le créateur peut utiliser cette commande.")
    bot.shop_channel_id = salon.id
    await ctx.send(f"✅ Salon des offres défini : {salon.mention}")
    save_data()


@bot.command()
async def set_salon_gemmes(ctx, salon: discord.TextChannel):
    if not is_owner(ctx):
        return await ctx.send(
            "❌ Seul le créateur peut utiliser cette commande.")
    msg = await salon.send("Initialisation des gemmes...")
    bot.gemmes_channel_id = salon.id
    bot.gemmes_message_id = msg.id
    await update_gemmes_message()
    await ctx.send("✅ Message de gemmes initialisé.")
    save_data()


# ───── Boutique ─────
class CategoryView(discord.ui.View):

    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author

    async def interaction_check(self, interaction):
        return interaction.user == self.author

    @discord.ui.button(label="🎬 Edits Shorts",
                       style=discord.ButtonStyle.blurple)
    async def shorts(self, interaction, button):
        await interaction.response.edit_message(content="Choisis une offre :",
                                                view=ShortsOffersView(
                                                    self.author))

    @discord.ui.button(label="🎮 Cache-Cache", style=discord.ButtonStyle.green)
    async def cache(self, interaction, button):
        await interaction.response.edit_message(content="Choisis une offre :",
                                                view=CacheCacheOffersView(
                                                    self.author))

    @discord.ui.button(label="🏆 Word Record", style=discord.ButtonStyle.red)
    async def wordrecord(self, interaction, button):
        await interaction.response.edit_message(content="Choisis une offre :",
                                                view=WROffersView(self.author))

    @discord.ui.button(label="✨ Rôle esthétique",
                       style=discord.ButtonStyle.gray)
    async def role(self, interaction, button):
        await interaction.response.edit_message(content="Choisis une offre :",
                                                view=RoleOffersView(
                                                    self.author))


class OfferButton(discord.ui.Button):

    def __init__(self, label, price, description, callback_fn):
        super().__init__(label=f"{label} ({price}💎)",
                         style=discord.ButtonStyle.primary)
        self.price = price
        self.description = description
        self.callback_fn = callback_fn

    async def callback(self, interaction):
        await self.callback_fn(interaction, self.price, self.description)


class BaseOffersView(discord.ui.View):

    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author

    async def interaction_check(self, interaction):
        return interaction.user == self.author


async def handle_offer(interaction,
                       price,
                       description,
                       is_role=False,
                       role_duration=None,
                       create_role=False):
    uid = str(interaction.user.id)

    if bot.user_gemmes.get(uid, 0) < price:
        await interaction.response.send_message(
            "❌ Tu n'as pas assez de gemmes !", ephemeral=True)
        return

    guild = interaction.guild

    if is_role:
        if create_role:
            existing = discord.utils.get(guild.roles,
                                         name=interaction.user.name)
            if existing:
                await interaction.response.send_message(
                    "❌ Tu as déjà un rôle personnalisé.", ephemeral=True)
                return
            role = await guild.create_role(name=interaction.user.name,
                                           colour=discord.Colour(0x8e44ad),
                                           mentionable=False)
        else:
            role = discord.utils.get(guild.roles, name="@@Ww")
            if role in interaction.user.roles:
                await interaction.response.send_message(
                    "❌ Tu as déjà ce rôle.", ephemeral=True)
                return

        bot.user_gemmes[uid] -= price
        await update_gemmes_message()
        save_data()

        await interaction.user.add_roles(role)
        await interaction.response.send_message(
            "✅ Offre achetée. Rôle ajouté !", ephemeral=True)

        if role_duration:
            await asyncio.sleep(role_duration)
            await interaction.user.remove_roles(role)
    else:
        bot.user_gemmes[uid] -= price
        await update_gemmes_message()
        save_data()

        salon = bot.get_channel(bot.shop_channel_id)
        if salon:
            await salon.send(
                f"{interaction.user.mention} a acheté : **{description}**\n<@&{ROLE_WW_ID}>"
            )
        await interaction.response.send_message("✅ Offre achetée !",
                                                ephemeral=True)


class ShortsOffersView(BaseOffersView):

    def __init__(self, author):
        super().__init__(author)
        self.add_item(OfferButton("1 clip", 80, "Edit 1 clip", handle_offer))
        self.add_item(OfferButton("2 clips", 110, "Edit 2 clips",
                                  handle_offer))


class CacheCacheOffersView(BaseOffersView):

    def __init__(self, author):
        super().__init__(author)
        self.add_item(
            OfferButton("4 manches", 150, "Cache-cache 4 manches",
                        handle_offer))
        self.add_item(
            OfferButton("6 manches", 200, "Cache-cache 6 manches",
                        handle_offer))


class WROffersView(BaseOffersView):

    def __init__(self, author):
        super().__init__(author)
        self.add_item(OfferButton("1 essai", 100, "WR 1 essai", handle_offer))
        self.add_item(OfferButton("2 essais", 170, "WR 2 essais",
                                  handle_offer))


class RoleOffersView(BaseOffersView):

    def __init__(self, author):
        super().__init__(author)
        self.add_item(
            OfferButton(
                "Ww (1 semaine)", 20, "Rôle @@Ww - 1 semaine",
                lambda i, p, d: handle_offer(
                    i, p, d, is_role=True, role_duration=7 * 24 * 3600)))
        self.add_item(
            OfferButton(
                "Ww (1 mois)", 50, "Rôle @@Ww - 1 mois",
                lambda i, p, d: handle_offer(
                    i, p, d, is_role=True, role_duration=30 * 24 * 3600)))
        self.add_item(
            OfferButton("Ww (permanent)", 100, "Rôle @@Ww - permanent",
                        lambda i, p, d: handle_offer(i, p, d, is_role=True)))
        self.add_item(
            OfferButton(
                "Rôle perso", 200, "Rôle personnalisé", lambda i, p, d:
                handle_offer(i, p, d, is_role=True, create_role=True)))


@bot.command()
async def shop(ctx):
    uid = str(ctx.author.id)
    gemmes = bot.user_gemmes.get(uid, 0)
    await ctx.send(f"Tu as **{gemmes} gemmes**.\nChoisis une catégorie :",
                   view=CategoryView(ctx.author))


# ───── Lancement ─────
async def main():
    await run_webserver()
    await bot.start(os.getenv("DISCORD_TOKEN"))


asyncio.run(main())
