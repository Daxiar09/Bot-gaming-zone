import discord
from discord.ext import commands, tasks
from discord.utils import get
from aiohttp import web
import asyncio
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="T.", intents=intents)

bot.user_gemmes = {}
bot.shop_channel_id = None
bot.gemmes_channel_id = None
bot.gemmes_message_id = None
bot.creator_id_by_guild = {}

# ───── Webserver pour Render ─────
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

# ───── Fonctions utilitaires ─────
async def update_gemmes_message(guild):
    if not bot.gemmes_channel_id or not bot.gemmes_message_id:
        return
    channel = guild.get_channel(bot.gemmes_channel_id)
    try:
        message = await channel.fetch_message(bot.gemmes_message_id)
    except:
        return
    lines = []
    for member in guild.members:
        if not member.bot:
            gemmes = bot.user_gemmes.get(str(member.id), 0)
            lines.append(f"{member.mention} : {gemmes} 💎")
    await message.edit(content="**💎 Gemmes des membres :**\n" + "\n".join(lines))

async def notify_creator(guild, text):
    if bot.shop_channel_id:
        channel = guild.get_channel(bot.shop_channel_id)
        if channel:
            owner = guild.owner
            await channel.send(f"{owner.mention} {text}")

# ───── Événement on_ready ─────
@bot.event
async def on_ready():
    print(f"{bot.user} est prêt !")
    for guild in bot.guilds:
        bot.creator_id_by_guild[guild.id] = guild.owner_id

# ───── Commandes Admin ─────
def is_guild_owner():
    async def predicate(ctx):
        return ctx.author.id == ctx.guild.owner_id
    return commands.check(predicate)

@bot.command()
@is_guild_owner()
async def set_salon_offres(ctx, salon: discord.TextChannel):
    bot.shop_channel_id = salon.id
    await ctx.send(f"✅ Salon d'offres défini : {salon.mention}")

@bot.command()
@is_guild_owner()
async def set_salon_gemmes(ctx, salon: discord.TextChannel):
    bot.gemmes_channel_id = salon.id
    message = await salon.send("Chargement des gemmes...")
    bot.gemmes_message_id = message.id
    await update_gemmes_message(ctx.guild)
    await ctx.send(f"✅ Salon de gemmes défini : {salon.mention}")

@bot.command()
@is_guild_owner()
async def addgemmes(ctx, membre: discord.Member, montant: int):
    user_id = str(membre.id)
    bot.user_gemmes[user_id] = bot.user_gemmes.get(user_id, 0) + montant
    await ctx.send(f"✅ {montant} gemmes ajoutées à {membre.mention}.")
    await update_gemmes_message(ctx.guild)

@bot.command()
@is_guild_owner()
async def deletegemmes(ctx, membre: discord.Member, montant: int):
    user_id = str(membre.id)
    bot.user_gemmes[user_id] = max(0, bot.user_gemmes.get(user_id, 0) - montant)
    await ctx.send(f"❌ {montant} gemmes retirées à {membre.mention}.")
    await update_gemmes_message(ctx.guild)

# ───── Boutique ─────
class OffreButton(discord.ui.Button):
    def __init__(self, label, gemmes, callback_fn):
        super().__init__(label=f"{label} - {gemmes}💎", style=discord.ButtonStyle.green)
        self.gemmes = gemmes
        self.callback_fn = callback_fn

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        current = bot.user_gemmes.get(user_id, 0)
        if current < self.gemmes:
            await interaction.response.send_message("❌ Tu n’as pas assez de gemmes.", ephemeral=True)
            return
        bot.user_gemmes[user_id] = current - self.gemmes
        await self.callback_fn(interaction)
        await update_gemmes_message(interaction.guild)

class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎬 Edits Shorts", style=discord.ButtonStyle.blurple)
    async def shorts(self, interaction, button):
        view = discord.ui.View()
        view.add_item(OffreButton("1 clip", 80, lambda i: notify_creator(i.guild, f"{i.user.mention} a acheté : Edit 1 clip")))
        view.add_item(OffreButton("2 clips", 110, lambda i: notify_creator(i.guild, f"{i.user.mention} a acheté : Edit 2 clips")))
        await interaction.response.send_message("**🎬 Edits Shorts :**", view=view, ephemeral=True)

    @discord.ui.button(label="🎮 Cache-Cache", style=discord.ButtonStyle.green)
    async def cache(self, interaction, button):
        view = discord.ui.View()
        view.add_item(OffreButton("4 manches", 150, lambda i: notify_creator(i.guild, f"{i.user.mention} a acheté : Cache-cache 4 manches")))
        view.add_item(OffreButton("8 manches", 250, lambda i: notify_creator(i.guild, f"{i.user.mention} a acheté : Cache-cache 8 manches")))
        await interaction.response.send_message("**🎮 Cache-cache :**", view=view, ephemeral=True)

    @discord.ui.button(label="🏆 Word Record", style=discord.ButtonStyle.red)
    async def wordrecord(self, interaction, button):
        view = discord.ui.View()
        view.add_item(OffreButton("1 essai", 100, lambda i: notify_creator(i.guild, f"{i.user.mention} a acheté : Word record 1 essai")))
        view.add_item(OffreButton("3 essais", 230, lambda i: notify_creator(i.guild, f"{i.user.mention} a acheté : Word record 3 essais")))
        await interaction.response.send_message("**🏆 Word Record :**", view=view, ephemeral=True)

    @discord.ui.button(label="✨ Rôle esthétique", style=discord.ButtonStyle.gray)
    async def role(self, interaction, button):
        view = discord.ui.View()
        async def add_role_temp(role_name, duration_days):
            async def action(i):
                guild = i.guild
                role = await guild.create_role(name=role_name)
                await i.user.add_roles(role)
                await i.response.send_message(f"✅ Tu as reçu le rôle `{role.name}` pour {duration_days} jours.", ephemeral=True)
                await asyncio.sleep(duration_days * 86400)
                await i.user.remove_roles(role)
                await role.delete()
            return action

        async def create_custom_role(i):
            guild = i.guild
            role = await guild.create_role(name=i.user.name)
            await i.user.add_roles(role)
            await i.response.send_message(f"✅ Rôle personnalisé `{role.name}` créé et attribué.", ephemeral=True)

        view.add_item(OffreButton("1 semaine", 20, await add_role_temp("@@Ww", 7)))
        view.add_item(OffreButton("1 mois", 50, await add_role_temp("@@Ww", 30)))
        view.add_item(OffreButton("Permanent", 100, lambda i: i.user.add_roles(get(i.guild.roles, name="@@Ww"))))
        view.add_item(OffreButton("Rôle personnalisé", 200, create_custom_role))
        await interaction.response.send_message("**✨ Rôles esthétiques :**", view=view, ephemeral=True)

@bot.command()
async def shop(ctx):
    await ctx.send("Voici les offres :", view=ShopView())

# ───── Lancement ─────
async def main():
    await run_webserver()
    await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())
