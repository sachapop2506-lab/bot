import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timezone
from utils import data_path

TICKETS_FILE = data_path("tickets.json")
CONFIG_FILE = data_path("ticket_config.json")

TICKET_CATEGORIES = [
    {"id": "sachatouille",  "label": "👤 Contacter Sachatouille",  "description": "Contacter directement Sachatouille"},
    {"id": "recrutement",   "label": "📋 Recrutements",            "description": "Candidater pour rejoindre l'équipe"},
    {"id": "giveaway",      "label": "🎁 Réclamation giveaway",    "description": "Réclamer un gain de giveaway"},
]


def load_tickets() -> dict:
    if os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_tickets(data: dict):
    with open(TICKETS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(data: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


class TicketCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=cat["label"],
                value=cat["id"],
                description=cat["description"],
            )
            for cat in TICKET_CATEGORIES
        ]
        super().__init__(
            placeholder="Choisissez le type de votre demande...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_category_select",
        )

    async def callback(self, interaction: discord.Interaction):
        category_id = self.values[0]
        category = next((c for c in TICKET_CATEGORIES if c["id"] == category_id), None)
        if not category:
            await interaction.response.send_message("❌ Catégorie invalide.", ephemeral=True)
            return

        config = load_config()
        guild_config = config.get(str(interaction.guild_id))
        if not guild_config:
            await interaction.response.send_message(
                "❌ Le système de tickets n'est pas configuré. Utilisez `/ticket setup`.", ephemeral=True
            )
            return

        tickets = load_tickets()
        guild_tickets = {
            k: v for k, v in tickets.items()
            if v.get("guild_id") == str(interaction.guild_id)
            and v.get("user_id") == str(interaction.user.id)
            and not v.get("closed")
        }
        if guild_tickets:
            existing_channel_id = list(guild_tickets.values())[0]["channel_id"]
            await interaction.response.send_message(
                f"❌ Tu as déjà un ticket ouvert : <#{existing_channel_id}>", ephemeral=True
            )
            return

        await interaction.response.send_message("⏳ Création de ton ticket...", ephemeral=True)

        staff_role_id = guild_config.get("staff_role_id")
        category_channel_id = guild_config.get("category_id")

        guild = interaction.guild
        staff_role = guild.get_role(int(staff_role_id)) if staff_role_id else None
        ticket_category = guild.get_channel(int(category_channel_id)) if category_channel_id else None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                read_message_history=True,
            ),
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
            )

        ticket_number = guild_config.get("ticket_count", 0) + 1
        channel_name = f"ticket-{ticket_number:04d}-{interaction.user.name[:10].lower()}"

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                category=ticket_category,
                overwrites=overwrites,
                topic=f"Ticket de {interaction.user} | Catégorie: {category['label']}",
            )
        except discord.Forbidden:
            await interaction.edit_original_response(
                content="❌ Je n'ai pas la permission de créer des salons."
            )
            return

        config[str(interaction.guild_id)]["ticket_count"] = ticket_number
        save_config(config)

        tickets[str(channel.id)] = {
            "channel_id": str(channel.id),
            "guild_id": str(guild.id),
            "user_id": str(interaction.user.id),
            "category": category_id,
            "category_label": category["label"],
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "closed": False,
        }
        save_tickets(tickets)

        embed = discord.Embed(
            title=f"{category['label']} — Ticket #{ticket_number:04d}",
            description=(
                f"Bonjour {interaction.user.mention}, bienvenue dans ton ticket !\n\n"
                f"Le staff va te répondre dès que possible. "
                f"En attendant, décris ta demande en détail.\n\n"
                f"Pour fermer ce ticket, clique sur le bouton ci-dessous."
            ),
            color=discord.Color.green(),
            timestamp=datetime.now(tz=timezone.utc),
        )
        embed.set_footer(text=f"Ticket créé par {interaction.user}")

        staff_mention = staff_role.mention if staff_role else "Staff"
        await channel.send(
            content=f"{interaction.user.mention} | {staff_mention}",
            embed=embed,
            view=TicketCloseView(),
        )

        await interaction.edit_original_response(
            content=f"✅ Ton ticket a été créé : {channel.mention}"
        )


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())


class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 Fermer le ticket",
        style=discord.ButtonStyle.red,
        custom_id="ticket_close",
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        tickets = load_tickets()
        key = str(interaction.channel_id)

        if key not in tickets:
            await interaction.response.send_message("❌ Ce salon n'est pas un ticket.", ephemeral=True)
            return

        ticket = tickets[key]
        is_creator = str(interaction.user.id) == ticket.get("user_id")
        config = load_config()
        guild_config = config.get(str(interaction.guild_id), {})
        staff_role_id = guild_config.get("staff_role_id")
        staff_role = interaction.guild.get_role(int(staff_role_id)) if staff_role_id else None
        is_staff = staff_role and staff_role in interaction.user.roles

        if not is_creator and not is_staff and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Seul le créateur du ticket ou un membre du staff peut fermer ce ticket.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message("🔒 Fermeture du ticket dans 5 secondes...")

        tickets[key]["closed"] = True
        tickets[key]["closed_by"] = str(interaction.user.id)
        tickets[key]["closed_at"] = datetime.now(tz=timezone.utc).isoformat()
        save_tickets(tickets)

        import asyncio
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason=f"Ticket fermé par {interaction.user}")
        except discord.Forbidden:
            await interaction.channel.send("❌ Je n'ai pas la permission de supprimer ce salon.")


class TicketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ticket_group = app_commands.Group(name="ticket", description="Système de tickets")

    @ticket_group.command(name="setup", description="Configurer le système de tickets")
    @app_commands.describe(
        salon="Salon où envoyer le panneau de tickets",
        role_staff="Rôle du staff qui peut voir et gérer les tickets",
        categorie="Catégorie Discord où créer les salons de tickets (optionnel)",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(
        self,
        interaction: discord.Interaction,
        salon: discord.TextChannel,
        role_staff: discord.Role,
        categorie: discord.CategoryChannel = None,
    ):
        config = load_config()
        config[str(interaction.guild_id)] = {
            "panel_channel_id": str(salon.id),
            "staff_role_id": str(role_staff.id),
            "category_id": str(categorie.id) if categorie else None,
            "ticket_count": config.get(str(interaction.guild_id), {}).get("ticket_count", 0),
        }
        save_config(config)

        embed = discord.Embed(
            title="🎫 Système de Tickets",
            description=(
                "Besoin d'aide ? Ouvre un ticket en sélectionnant la catégorie "
                "qui correspond à ta demande dans le menu ci-dessous.\n\n"
                "Un membre du staff te répondra dès que possible."
            ),
            color=discord.Color.blurple(),
        )
        for cat in TICKET_CATEGORIES:
            embed.add_field(name=cat["label"], value=cat["description"], inline=True)
        embed.set_footer(text="Un seul ticket ouvert à la fois par membre.")

        await salon.send(embed=embed, view=TicketPanelView())
        await interaction.response.send_message(
            f"✅ Panneau de tickets envoyé dans {salon.mention} !\n"
            f"Role staff : {role_staff.mention}",
            ephemeral=True,
        )

    @ticket_group.command(name="fermer", description="Fermer le ticket actuel")
    async def fermer(self, interaction: discord.Interaction):
        tickets = load_tickets()
        key = str(interaction.channel_id)
        if key not in tickets or tickets[key].get("closed"):
            await interaction.response.send_message("❌ Ce salon n'est pas un ticket actif.", ephemeral=True)
            return

        ticket = tickets[key]
        config = load_config()
        guild_config = config.get(str(interaction.guild_id), {})
        staff_role_id = guild_config.get("staff_role_id")
        staff_role = interaction.guild.get_role(int(staff_role_id)) if staff_role_id else None
        is_staff = staff_role and staff_role in interaction.user.roles
        is_creator = str(interaction.user.id) == ticket.get("user_id")

        if not is_creator and not is_staff and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Seul le créateur ou un membre du staff peut fermer ce ticket.", ephemeral=True
            )
            return

        await interaction.response.send_message("🔒 Fermeture du ticket dans 5 secondes...")
        tickets[key]["closed"] = True
        tickets[key]["closed_by"] = str(interaction.user.id)
        tickets[key]["closed_at"] = datetime.now(tz=timezone.utc).isoformat()
        save_tickets(tickets)

        import asyncio
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason=f"Ticket fermé par {interaction.user}")
        except discord.Forbidden:
            await interaction.channel.send("❌ Je n'ai pas la permission de supprimer ce salon.")

    @ticket_group.command(name="ajouter", description="Ajouter un membre au ticket")
    @app_commands.describe(membre="Le membre à ajouter")
    async def ajouter(self, interaction: discord.Interaction, membre: discord.Member):
        tickets = load_tickets()
        key = str(interaction.channel_id)
        if key not in tickets or tickets[key].get("closed"):
            await interaction.response.send_message("❌ Ce salon n'est pas un ticket actif.", ephemeral=True)
            return

        config = load_config()
        guild_config = config.get(str(interaction.guild_id), {})
        staff_role_id = guild_config.get("staff_role_id")
        staff_role = interaction.guild.get_role(int(staff_role_id)) if staff_role_id else None
        is_staff = staff_role and staff_role in interaction.user.roles

        if not is_staff and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Seul le staff peut ajouter des membres.", ephemeral=True)
            return

        await interaction.channel.set_permissions(
            membre,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
        )
        await interaction.response.send_message(f"✅ {membre.mention} a été ajouté au ticket.")

    @ticket_group.command(name="retirer", description="Retirer un membre du ticket")
    @app_commands.describe(membre="Le membre à retirer")
    async def retirer(self, interaction: discord.Interaction, membre: discord.Member):
        tickets = load_tickets()
        key = str(interaction.channel_id)
        if key not in tickets or tickets[key].get("closed"):
            await interaction.response.send_message("❌ Ce salon n'est pas un ticket actif.", ephemeral=True)
            return

        config = load_config()
        guild_config = config.get(str(interaction.guild_id), {})
        staff_role_id = guild_config.get("staff_role_id")
        staff_role = interaction.guild.get_role(int(staff_role_id)) if staff_role_id else None
        is_staff = staff_role and staff_role in interaction.user.roles

        if not is_staff and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Seul le staff peut retirer des membres.", ephemeral=True)
            return

        if str(membre.id) == tickets[key].get("user_id"):
            await interaction.response.send_message("❌ Impossible de retirer le créateur du ticket.", ephemeral=True)
            return

        await interaction.channel.set_permissions(membre, overwrite=None)
        await interaction.response.send_message(f"✅ {membre.mention} a été retiré du ticket.")

    @setup.error
    async def setup_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Tu n'as pas la permission `Administrateur`.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(TicketCog(bot))
    bot.add_view(TicketPanelView())
    bot.add_view(TicketCloseView())
