import discord
from discord.ext import commands
from discord import app_commands
import os
import random
import json
from datetime import datetime

intents = discord.Intents. default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ROLE_1_ID = 1462038513070506140
ROLE_2_ID = 1462038917707730984
TROPHY_EMOJI = "<:TROPHY:1462058671512223967>"
CROSS_EMOJI = "<:sg_cross:1462063961972277309>"
CHECK_EMOJI = "<:sg_check:1462063999112970281>"
VS_EMOJI = "<:VS:1462058544583938099>"

class Tournament:
    def __init__(self, guild_id, message_id=None):
        self.guild_id = guild_id
        self.message_id = message_id
        self.players = []
        self.max_players = 0
        self.active = False
        self.channel = None
        self.target_channel = None
        self. message = None
        self.rounds = []
        self.results = []
        self.eliminated = []
        self.fake_count = 1
        self.map = ""
        self.abilities = ""
        self.region = ""
        self.prize_1st = ""
        self.prize_2nd = ""
        self.prize_3rd = ""
        self.prize_4th = ""
        self.title = ""
        self.mode = "1v1"
        self.match_winners = {}

tournaments = {}
active_tournament_ids = {}

def get_tournament(guild_id, message_id=None):
    if message_id is None:
        message_id = active_tournament_ids.get(guild_id)
    
    key = (guild_id, message_id)
    if key not in tournaments: 
        if message_id is None:  return None
        tournaments[key] = Tournament(guild_id, message_id)
    return tournaments[key]

balances = {}
DASH_GEM_EMOJI = "<: Dashgems:1462085260413243464>"
GEMS_EMOJI = "<:Gems:1462455236487811308>"
STAR_ICON = "<:starIcon:1462455325230895278>"
SHOP_LOG_CHANNEL_ID = 1462794902814326887

teams = {}
team_invitations = {}
player_teams = {}
log_channels = {}
bracket_roles = {}
host_registrations = {
    'active': False,
    'max_hosters': 0,
    'hosters': [],
    'channel': None,
    'message': None
}

def save_data():
    """Save all data to JSON file"""
    try: 
        data = {
            'log_channels': log_channels,
            'bracket_roles': bracket_roles,
            'balances': balances
        }
        with open('user_data.json', 'w') as f:
            json. dump(data, f, indent=4)
    except Exception as e: 
        print(f"Error saving data: {e}")

def load_data():
    global log_channels, bracket_roles, balances
    try:
        with open('user_data.json', 'r') as f:
            data = json.load(f)
            log_channels = data.get('log_channels', {})
            bracket_roles = data.get('bracket_roles', {})
            balances = data.get('balances', {})
    except FileNotFoundError: 
        pass

async def auto_delete(ctx):
    try:
        if isinstance(ctx, commands.Context):
            await ctx.message.delete()
    except:
        pass

class ShopConfirmView(discord.ui.View):
    def __init__(self, item_name, cost, gems_amount):
        super().__init__(timeout=60)
        self.item_name = item_name
        self. cost = cost
        self.gems_amount = gems_amount
        self.submited = False

    @discord.ui.button(label="Yes", style=discord.ButtonStyle. green, emoji=CHECK_EMOJI)
    async def confirm(self, interaction: discord. Interaction, button: discord.ui. Button):
        user_id = str(interaction.user.id)
        if balances.get(user_id, 0) < self.cost:
            return await interaction.response.send_message(f"{CROSS_EMOJI} You don't have enough dash gems!", ephemeral=True)
        
        balances[user_id] -= self.cost
        save_data()
        
        embed = discord.Embed(
            title="Purchase Confirmed",
            description=f"You confirmed the purchase of **{self.item_name}**. Please enter your in game name by clicking the button below.",
            color=0x3498db
        )
        view = discord.ui.View()
        enter_button = discord.ui.Button(label="Enter name", style=discord.ButtonStyle. blurple, emoji=STAR_ICON)
        
        async def modal_callback(interaction: discord. Interaction):
            if self.submited:
                return await interaction.response.send_message("❌ You have already submitted your name for this purchase.", ephemeral=True)

            modal = discord.ui.Modal(title="In Game Name")
            name_input = discord.ui.TextInput(label="What is your in game name?", placeholder="Type here.. .", min_length=1)
            modal.add_item(name_input)
            
            async def on_submit(interaction: discord. Interaction):
                if self.submited:
                    return await interaction.response.send_message("❌ You have already submitted your name for this purchase.", ephemeral=True)
                
                self.submited = True
                enter_button.disabled = True
                await interaction.message.edit(view=view)

                channel = bot.get_channel(SHOP_LOG_CHANNEL_ID)
                if channel:
                    log_embed = discord.Embed(
                        description=f"{CHECK_EMOJI} **{interaction.user.name}** purchased **{self.item_name}**. His in game name is:\n```{name_input.value}```",
                        color=0x00ff00
                    )
                    await channel.send(embed=log_embed)
                await interaction.response.send_message("✅ Success! Your purchase has been logged.", ephemeral=True)
            
            modal.on_submit = on_submit
            await interaction.response.send_modal(modal)

        enter_button.callback = modal_callback
        view.add_item(enter_button)
        
        try:
            await interaction.user. send(embed=embed, view=view)
            await interaction.response.edit_message(content="✅ Purchase confirmed!  Check your DMs.", view=None)
        except discord. Forbidden:
            await interaction.response.edit_message(content="❌ I couldn't DM you. Please open your DMs and try again.", view=None)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red, emoji=CROSS_EMOJI)
    async def cancel(self, interaction: discord. Interaction, button: discord.ui.Button):
        await interaction. response.edit_message(content="❌ Purchase cancelled.", view=None)

class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def handle_buy(self, interaction, cost, gems_amount, label):
        user_id = str(interaction.user.id)
        balance = balances.get(user_id, 0)
        if balance < cost:
            return await interaction.response.send_message(f"{CROSS_EMOJI} You don't have enough dash gems to buy this!", ephemeral=True)
        
        view = ShopConfirmView(label, cost, gems_amount)
        await interaction.response.send_message(f"Are you sure you want to buy **{label}**? ", view=view, ephemeral=True)

    @discord.ui.button(label="200 Gems", style=discord. ButtonStyle.blurple, emoji="<:Gems:1462455236487811308>")
    async def buy_200(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_buy(interaction, 2500, 200, button.label)

    @discord.ui.button(label="400 Gems", style=discord. ButtonStyle.blurple, emoji="<:Gems:1462455236487811308>")
    async def buy_400(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_buy(interaction, 5000, 400, button.label)

    @discord.ui.button(label="800 Gems", style=discord. ButtonStyle.blurple, emoji="<:Gems:1462455236487811308>")
    async def buy_800(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_buy(interaction, 10000, 800, button.label)

def has_permission_level_1(user:  discord.Member) -> bool:
    try:
        if user.guild_permissions.administrator:
            return True
        return any(r.id in [ROLE_1_ID, ROLE_2_ID] for r in user.roles)
    except Exception:
        return False

def has_permission_level_2(user: discord.Member) -> bool:
    try:
        if user.guild_permissions.administrator:
            return True
        return any(r.id == ROLE_2_ID for r in user.roles)
    except Exception:
        return False

class FakePlayer:
    def __init__(self, name, user_id, placeholder=False):
        self.display_name = name
        self. id = user_id
        self. name = name
        self.nick = None
        self.placeholder = placeholder

def get_player_display_name(player, guild_id=None, bold=True):
    if isinstance(player, FakePlayer):
        return player.name
    
    name = player.name if hasattr(player, 'name') else str(player)
    
    emojis = []
    if guild_id:
        guild_str = str(guild_id)
        if guild_str in bracket_roles and hasattr(player, 'roles'):
            for role in player. roles:
                role_str = str(role. id)
                if role_str in bracket_roles[guild_str]:
                    emojis. append(bracket_roles[guild_str][role_str])
            
    if bold:
        name_with_emojis = f"**{name}** {' '.join(emojis)}" if emojis else f"**{name}**"
    else:
        name_with_emojis = f"{name} {' '.join(emojis)}" if emojis else f"{name}"
    return name_with_emojis

@bot.command()
async def bracketname(ctx, member: discord.Member = None):
    member = member or ctx.author
    formatted_name = get_player_display_name(member, ctx.guild.id, bold=False)
    try:
        await member.send(f"Your bracketname is **{formatted_name}**")
        if member != ctx.author:
            await ctx.send(f"✅ Sent bracketname to {member.mention}'s DMs.")
        else:
            await ctx.send("✅ Sent your bracketname to your DMs.", delete_after=5)
    except discord.Forbidden:
        await ctx.send(f"❌ I couldn't send a DM to {member.mention}.  They might have DMs closed.")

def get_team_id(guild_id, user_id):
    guild_str = str(guild_id)
    return player_teams.get(guild_str, {}).get(str(user_id))

def get_team_members(guild_id, team_id):
    guild_str = str(guild_id)
    return teams.get(guild_str, {}).get(team_id, [])

def get_teammate(guild_id, user_id):
    team_id = get_team_id(guild_id, user_id)
    if not team_id:
        return None
    team_members = get_team_members(guild_id, team_id)
    for member in team_members:
        if member. id != user_id:
            return member
    return None

def create_team(guild_id, player1, player2):
    guild_str = str(guild_id)
    if guild_str not in teams:  
        teams[guild_str] = {}
        player_teams[guild_str] = {}
    team_id = f"team_{len(teams[guild_str]) + 1}_{guild_id}"
    teams[guild_str][team_id] = [player1, player2]
    player_teams[guild_str][str(player1.id)] = team_id
    player_teams[guild_str][str(player2.id)] = team_id
    return team_id

def remove_team(guild_id, team_id):
    guild_str = str(guild_id)
    if guild_str in teams and team_id in teams[guild_str]:
        for player in teams[guild_str][team_id]:
            if str(player.id) in player_teams. get(guild_str, {}):
                del player_teams[guild_str][str(player.id)]
        del teams[guild_str][team_id]

def get_team_display_name(guild_id, team_members):
    if len(team_members) == 2:
        name1 = get_player_display_name(team_members[0], guild_id)
        name2 = get_player_display_name(team_members[1], guild_id)
        return f"{name1} & {name2}"
    return "Unknown Team"

async def log_command(guild_id, user, command, details=""):
    guild_str = str(guild_id)
    if guild_str not in log_channels:
        return
    try:
        channel = bot.get_channel(log_channels[guild_str])
        if not channel:
            return
        embed = discord.Embed(
            title="📋 Tournament Command Used",
            color=0x3498db,
            timestamp=datetime.now()
        )
        embed.add_field(name="User", value=getattr(user, "name", str(user)), inline=True)
        embed.add_field(name="Command", value=command, inline=True)
        if details:
            embed.add_field(name="Details", value=details, inline=False)
        await channel.send(embed=embed)
    except Exception:  
        pass

class InviteView(discord.ui. View):
    def __init__(self, inviter, inviter_guild_id, *, persistent: bool = False):
        super().__init__(timeout=None if persistent else 300)
        self.inviter = inviter
        self.inviter_guild_id = inviter_guild_id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle. green, emoji=CHECK_EMOJI, custom_id="invite_accept")
    async def accept_button(self, interaction: discord. Interaction, button: discord.ui. Button):
        guild_str = str(self.inviter_guild_id) if self.inviter_guild_id else None
        if not self.inviter or not guild_str:
            await interaction.response.send_message(f"{CROSS_EMOJI} Invitation expired or is invalid.", ephemeral=True)
            return
        inviter_team_id = get_team_id(self.inviter_guild_id, self.inviter.id)
        if inviter_team_id: 
            await interaction.response.send_message(f"{CROSS_EMOJI} The inviter is already in a team.", ephemeral=True)
            return
        invitee_team_id = get_team_id(self.inviter_guild_id, interaction.user.id)
        if invitee_team_id:
            await interaction.response.send_message(f"{CROSS_EMOJI} You are already in a team.", ephemeral=True)
            return
        create_team(self.inviter_guild_id, self.inviter, interaction.user)
        if guild_str in team_invitations and str(interaction.user.id) in team_invitations[guild_str]: 
            if self.inviter. id in team_invitations[guild_str][str(interaction.user.id)]:
                team_invitations[guild_str][str(interaction.user.id)]. remove(self.inviter.id)
        await interaction.response.send_message(f"{CHECK_EMOJI} You accepted the invitation!   Team created: {self.inviter.name} & {interaction.user.name}!", ephemeral=True)

    @discord.ui.button(label="Decline", style=discord. ButtonStyle.red, emoji=CROSS_EMOJI, custom_id="invite_decline")
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_str = str(self. inviter_guild_id) if self.inviter_guild_id else None
        invitee_str = str(interaction.user.id)
        if guild_str and guild_str in team_invitations and invitee_str in team_invitations[guild_str]:  
            if self.inviter and self.inviter.id in team_invitations[guild_str][invitee_str]:
                team_invitations[guild_str][invitee_str].remove(self.inviter.id)
        await interaction.response.send_message(f"{CROSS_EMOJI} You declined the invitation from {self.inviter.name if self.inviter else 'the inviter'}.", ephemeral=True)

class WinnersView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(label="Winners", style=discord.ButtonStyle. primary, custom_id="show_winners", emoji=TROPHY_EMOJI)
    async def show_winners(self, interaction: discord.Interaction, button: discord.ui.Button):
        tournament = get_tournament(self.guild_id, interaction.message.id)
        if not tournament. active:
            await interaction.response. send_message(f"{CROSS_EMOJI} No active tournament.", ephemeral=True)
            return
        current_round = tournament.rounds[-1] if tournament.rounds else []
        round_number = len(tournament.rounds)
        winners_text = f"**Round {round_number} Winners:**\n\n"
        for i, match in enumerate(current_round, 1):
            match_key = f"round_{round_number}_match_{i}"
            if match_key in tournament.match_winners:
                winner = tournament.match_winners[match_key]
                if tournament.mode == "2v2": 
                    winner_display = get_team_display_name(self.guild_id, winner)
                else:
                    winner_display = get_player_display_name(winner, self.guild_id)
                winners_text += f"Match {i}: **{winner_display}**\n"
            else:  
                winners_text += f"Match {i}: **?  **\n"
        await interaction.response.send_message(winners_text, ephemeral=True)

class TournamentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

    @discord.ui.button(label="Register", style=discord.ButtonStyle. green, custom_id="tournament_register", emoji=CHECK_EMOJI)
    async def register_button(self, interaction:  discord.Interaction, button: discord.ui.Button):
        try:
            tournament = get_tournament(interaction.guild.id, interaction.message.id)
            if not tournament: 
                return await interaction.response.send_message(f"{CROSS_EMOJI} Tournament data not found for this message.", ephemeral=True)
            if tournament.max_players == 0:
                return await interaction.response.send_message(f"{CROSS_EMOJI} This tournament is not correctly initialized.", ephemeral=True)
            if tournament.active:
                return await interaction.response.send_message("⚠️ Tournament already started.", ephemeral=True)

            if tournament.mode == "2v2":
                team_id = get_team_id(interaction.guild.id, interaction.user.id)
                if not team_id:
                    return await interaction. response.send_message(f"{CROSS_EMOJI} You need to be in a team to register for 2v2 tournaments!   Use `!invite @teammate` to create a team.", ephemeral=True)
                team_members = get_team_members(interaction.guild.id, team_id)
                if any(member in tournament.players for member in team_members):
                    return await interaction.response. send_message(f"{CROSS_EMOJI} Your team is already registered.", ephemeral=True)
                current_teams = len(tournament.players) // 2
                if current_teams >= tournament.max_players:
                    return await interaction.response.send_message(f"{CROSS_EMOJI} Tournament is full.", ephemeral=True)
                tournament.players.extend(team_members)
                await self.update_tournament_embed(interaction, tournament)
                await interaction. response.send_message(f"{CHECK_EMOJI} Team registered!  ({len(tournament.players) // 2}/{tournament.max_players} teams)", ephemeral=True)
            else:
                if interaction.user in tournament.players:
                    return await interaction.response.send_message(f"{CROSS_EMOJI} You are already registered.", ephemeral=True)
                if len(tournament.players) >= tournament.max_players:
                    return await interaction.response.send_message(f"{CROSS_EMOJI} Tournament is full.", ephemeral=True)
                tournament.players.append(interaction.user)
                await self.update_tournament_embed(interaction, tournament)
                await interaction.response.send_message(f"{CHECK_EMOJI} Registered! ({len(tournament.players)}/{tournament.max_players})", ephemeral=True)
        except Exception as e:
            print(f"TournamentView. register_button error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"{CROSS_EMOJI} An error occurred.", ephemeral=True)

    @discord.ui.button(label="Unregister", style=discord.ButtonStyle.red, custom_id="tournament_unregister", emoji=CROSS_EMOJI)
    async def unregister_button(self, interaction: discord. Interaction, button: discord.ui.Button):
        try:
            tournament = get_tournament(interaction.guild.id, interaction.message.id)
            if not tournament:
                return await interaction.response.send_message(f"{CROSS_EMOJI} Tournament data not found for this message.", ephemeral=True)
            if tournament. max_players == 0:
                return await interaction.response.send_message(f"{CROSS_EMOJI} This tournament is not correctly initialized.", ephemeral=True)
            if tournament.active:
                return await interaction.response.send_message("⚠️ Tournament already started.", ephemeral=True)

            if tournament.mode == "2v2":  
                team_id = get_team_id(interaction.guild.id, interaction.user.id)
                if not team_id:  
                    return await interaction. response.send_message(f"{CROSS_EMOJI} You are not in a team.", ephemeral=True)
                team_members = get_team_members(interaction.guild.id, team_id)
                if not any(member in tournament.players for member in team_members):
                    return await interaction.response.send_message(f"{CROSS_EMOJI} Your team is not registered.", ephemeral=True)
                for member in team_members:
                    if member in tournament.players:
                        tournament.players.remove(member)
                await self.update_tournament_embed(interaction, tournament)
                await interaction.response.send_message(f"{CHECK_EMOJI} Team unregistered!   ({len(tournament.players) // 2}/{tournament.max_players} teams)", ephemeral=True)
            else:
                if interaction.user not in tournament.players:
                    return await interaction.response.send_message(f"{CROSS_EMOJI} You are not registered.", ephemeral=True)
                tournament.players.remove(interaction.user)
                await self.update_tournament_embed(interaction, tournament)
                await interaction.response.send_message(f"{CHECK_EMOJI} Unregistered! ({len(tournament.players)}/{tournament.max_players})", ephemeral=True)
        except Exception as e:
            print(f"TournamentView.unregister_button error: {e}")
            if not interaction.response. is_done():
                await interaction.response.send_message(f"{CROSS_EMOJI} An error occurred.", ephemeral=True)

    async def update_tournament_embed(self, interaction, tournament):
        try:
            message = tournament.message
            if not message:
                if interaction.message: 
                    message = interaction.message
                else:
                    return
            
            current_count = len(tournament.players) if tournament.mode == "1v1" else len(tournament. players) // 2
            players_label = "**👥 Players:**" if tournament. mode == "1v1" else "**👥 Teams:**"

            embed = discord.Embed(
                title=f"{TROPHY_EMOJI} **{tournament.title}** {TROPHY_EMOJI}",
                color=0x00ff00
            )

            info = (
                f"{players_label} **{current_count}/{tournament.max_players}**\n"
                f"🗺️ **Map:** {tournament.map}\n"
                f"⚡ **Abilities:** {tournament.abilities}\n"
                f"🎯 **Mode:** {tournament.mode}\n"
                f"🌍 **Region:** {tournament.region}\n\n"
                f"<: Crown:1462065099622842450> **Prizes** <:Crown:1462065099622842450>\n"
                f"🥇 1st:  {tournament.prize_1st}\n"
                f"🥈 2nd: {tournament. prize_2nd}\n"
                f"🥉 3rd: {tournament.prize_3rd}\n"
                f"🏅 4th: {tournament.prize_4th}"
            )

            embed.description = info
            embed.set_image(url="https://cdn.discordapp.com/attachments/1462029238528905219/1462109996480200765/Screenshot_20260117-174158-7852. png? ex=696cff8b&is=696bae0b&hm=6e4e4d8907016b5fc5652eb01ad3e33eb0624f10593d4730ef7e3c3ab34d4765")
            
            try:
                await message.edit(embed=embed)
                tournament.message = message
            except Exception as e:
                print(f"Error editing message: {e}")
        except Exception as e:
            print(f"update_tournament_embed error: {e}")

class HosterRegistrationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Register as Hoster", style=discord. ButtonStyle.green, custom_id="hoster_register")
    async def register_hoster(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not host_registrations['active']:
            return await interaction.response.send_message("❌ Host registration is not active.", ephemeral=True)
        if interaction.user in host_registrations['hosters']:
            return await interaction. response.send_message("❌ You are already registered as a hoster.", ephemeral=True)
        if len(host_registrations['hosters']) >= host_registrations['max_hosters']:
            return await interaction.response.send_message("❌ Maximum hosters reached.", ephemeral=True)
        host_registrations['hosters'].append(interaction.user)
        embed = discord.Embed(title="🎯 Hoster Registration", description="Register here to become a tournament hoster!", color=0x00ff00)
        if host_registrations['hosters']:  
            hoster_list = ""
            for i, hoster in enumerate(host_registrations['hosters'], 1):
                hoster_list += f"{i}. {hoster.name}\n"
            embed.add_field(name="Hosters registered:", value=hoster_list, inline=False)
        else:
            embed.add_field(name="Hosters registered:", value="None yet", inline=False)
        embed.add_field(name="Slots:", value=f"{len(host_registrations['hosters'])}/{host_registrations['max_hosters']}", inline=True)
        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send(f"✅ {interaction.user.name} registered as hoster.", ephemeral=True)

    @discord.ui.button(label="Unregister", style=discord.ButtonStyle.red, custom_id="hoster_unregister")
    async def unregister_hoster(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not host_registrations['active']:
            return await interaction.response.send_message("❌ Host registration is not active.", ephemeral=True)
        if interaction.user not in host_registrations['hosters']:
            return await interaction.response.send_message("❌ You are not registered as a hoster.", ephemeral=True)
        host_registrations['hosters'].remove(interaction.user)
        embed = discord.Embed(title="🎯 Hoster Registration", description="Register here to become a tournament hoster!", color=0x00ff00)
        if host_registrations['hosters']: 
            hoster_list = ""
            for i, hoster in enumerate(host_registrations['hosters'], 1):
                hoster_list += f"{i}. {hoster.name}\n"
            embed.add_field(name="Hosters registered:", value=hoster_list, inline=False)
        else:
            embed.add_field(name="Hosters registered:", value="None yet", inline=False)
        embed.add_field(name="Slots:", value=f"{len(host_registrations['hosters'])}/{host_registrations['max_hosters']}", inline=True)
        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send(f"✅ {interaction.user.name} unregistered from hosting.", ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ Bot online as {bot.user}")
    load_data()
    bot.add_view(TournamentView())
    bot.add_view(HosterRegistrationView())
    bot.add_view(InviteView(None, None, persistent=True))
    bot.add_view(WinnersView(0))
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def add_dash(ctx, member: discord.Member, amount: int):
    user_id = str(member.id)
    balances[user_id] = balances.get(user_id, 0) + amount
    save_data()
    embed = discord.Embed(
        description=f"{CHECK_EMOJI} Successfully added **{amount}** {DASH_GEM_EMOJI} to {member.mention}!",
        color=0x00ff00
    )
    await ctx.send(embed=embed)
    await auto_delete(ctx)

@bot.command()
@commands.has_permissions(administrator=True)
async def remove_dash(ctx, member: discord.Member, amount: int):
    user_id = str(member.id)
    balances[user_id] = max(0, balances.get(user_id, 0) - amount)
    save_data()
    embed = discord.Embed(
        description=f"{CHECK_EMOJI} Successfully removed **{amount}** {DASH_GEM_EMOJI} from {member.mention}!",
        color=0x00ff00
    )
    await ctx.send(embed=embed)
    await auto_delete(ctx)

@bot.command()
async def shop(ctx):
    user_id = str(ctx.author.id)
    balance = balances.get(user_id, 0)
    embed = discord.Embed(
        title="### Stumble Zone || Gems Shop",
        description=(
            f"{ctx.author.mention}, welcome to our **Stumble Zone Shop**! Please click under this messages, what you would like to buy.  {STAR_ICON}\n\n"
            f"Your current balance is: **{balance}** {DASH_GEM_EMOJI}\n\n"
            f"**2500 {DASH_GEM_EMOJI} - 200 {GEMS_EMOJI}\n"
            f"5000 {DASH_GEM_EMOJI} - 400 {GEMS_EMOJI}\n"
            f"10000 {DASH_GEM_EMOJI} - 800 {GEMS_EMOJI}**"
        ),
        color=0x3498db
    )
    view = ShopView()
    await ctx.send(embed=embed, view=view)
    await auto_delete(ctx)

@bot.command()
async def signed(ctx):
    signed_text = ""
    found = False
    for (gid, mid), tour in tournaments.items():
        if gid == ctx.guild.id and tour.max_players > 0:
            found = True
            current_count = len(tour.players) if tour.mode == "1v1" else len(tour.players) // 2
            signed_text += f"**Tournament:  {tour.title}** ({current_count}/{tour.max_players})\n"
            if tour.mode == "1v1":
                for p in tour.players:
                    signed_text += f"- {p.name}\n"
            else:
                for i in range(0, len(tour.players), 2):
                    if i + 1 < len(tour. players):
                        signed_text += f"- {tour.players[i].name} & {tour.players[i+1].name}\n"
            signed_text += "\n"
    
    if not found:
        await ctx.send("❌ No tournaments currently running.")
    else:
        embed = discord.Embed(title="📝 Registered Players/Teams", description=signed_text, color=0x3498db)
        await ctx.send(embed=embed)
    await auto_delete(ctx)

@bot.tree.command(name="tournament1v1", description="Create a 1v1 tournament")
@app_commands.describe(
    title="Tournament title (required)",
    number_of_players="Number of players (2, 4, 8, 16, or 32)",
    map="Map name",
    abilities="Abilities setting",
    region="Tournament region",
    first="1st place prize",
    second="2nd place prize",
    third="3rd place prize",
    fourth="4th place prize"
)
async def tournament1v1(
    interaction: discord.Interaction,
    title: str,
    number_of_players: int,
    map: str,
    abilities:  str,
    region: str,
    channel:  discord.TextChannel,
    first: str,
    second: str,
    third: str,
    fourth: str
):
    if not has_permission_level_2(interaction.user):
        return await interaction.response. send_message(f"{CROSS_EMOJI} You don't have permission to create tournaments.", ephemeral=True)
    if number_of_players not in [2, 4, 8, 16, 32]:  
        return await interaction.response.send_message(f"{CROSS_EMOJI} Players must be 2, 4, 8, 16, or 32!", ephemeral=True)
    
    view = TournamentView()
    msg = await channel.send(content="Creating tournament.. .", view=view)
    
    tournament = Tournament(interaction.guild. id, msg.id)
    tournaments[(interaction.guild.id, msg.id)] = tournament
    active_tournament_ids[interaction.guild.id] = msg.id
    
    tournament.max_players = number_of_players
    tournament.mode = "1v1"
    tournament.channel = interaction.channel
    tournament.target_channel = channel
    tournament.title = title
    tournament.map = map
    tournament.abilities = abilities
    tournament.region = region
    tournament.prize_1st = first
    tournament.prize_2nd = second
    tournament.prize_3rd = third
    tournament.prize_4th = fourth
    tournament.message = msg
    
    await view.update_tournament_embed(interaction, tournament)
    await msg.edit(content=None)
    
    await log_command(interaction. guild.id, interaction.user, f"/{interaction.command.name}", f"Mode: {tournament.mode}, Max:  {number_of_players}, Region: {region}, Channel: {channel.mention}")
    await interaction.response.send_message("✅ Tournament created successfully!", ephemeral=True)

@bot.tree.command(name="tournament2v2", description="Create a 2v2 tournament")
@app_commands.describe(
    title="Tournament title (required)",
    number_of_teams="Number of teams (2, 4, 8, or 16)",
    map="Map name",
    abilities="Abilities setting",
    region="Tournament region",
    first="1st place prize",
    second="2nd place prize",
    third="3rd place prize",
    fourth="4th place prize"
)
async def tournament2v2(
    interaction: discord.Interaction,
    title: str,
    number_of_teams: int,
    map: str,
    abilities: str,
    region:  str,
    channel: discord. TextChannel,
    first: str,
    second: str,
    third: str,
    fourth: str
):
    if not has_permission_level_2(interaction.user):
        return await interaction.response.send_message(f"{CROSS_EMOJI} You don't have permission to create tournaments.", ephemeral=True)
    if number_of_teams not in [2, 4, 8, 16]: 
        return await interaction.response. send_message(f"{CROSS_EMOJI} Teams must be 2, 4, 8, or 16!", ephemeral=True)

    view = TournamentView()
    msg = await channel.send(content="Creating tournament...", view=view)

    tournament = Tournament(interaction.guild.id, msg.id)
    tournaments[(interaction.guild.id, msg.id)] = tournament
    active_tournament_ids[interaction.guild.id] = msg. id

    tournament.max_players = number_of_teams
    tournament.mode = "2v2"
    tournament.channel = interaction.channel
    tournament.target_channel = channel
    tournament.title = title
    tournament.map = map
    tournament.abilities = abilities
    tournament.region = region
    tournament.prize_1st = first
    tournament.prize_2nd = second
    tournament.prize_3rd = third
    tournament.prize_4th = fourth
    tournament.message = msg

    await view.update_tournament_embed(interaction, tournament)
    await msg.edit(content=None)

    await log_command(interaction.guild.id, interaction. user, f"/{interaction.command.name}", f"Mode: {tournament.mode}, Max: {number_of_teams}, Region: {region}, Channel: {channel.mention}")
    await interaction.response. send_message("✅ Tournament created successfully!", ephemeral=True)

@bot.command()
async def bracketrole(ctx, role: discord.Role, emoji: str):
    if not has_permission_level_2(ctx.author):
         return await ctx.send(f"{CROSS_EMOJI} You don't have permission.", delete_after=5)
    
    guild_str = str(ctx.guild.id)
    if guild_str not in bracket_roles:
        bracket_roles[guild_str] = {}
    
    bracket_roles[guild_str][str(role.id)] = emoji
    save_data()
    await ctx.send(f"{CHECK_EMOJI} Role {role.name} linked to emoji {emoji}", delete_after=5)

@bot.command()
async def code1v1(ctx, member1: discord.Member, member2: discord.Member, *, code: str):
    try:
        await ctx.message.delete()
    except:
        pass
    if not has_permission_level_1(ctx.author):
        return await ctx.send(f"{CROSS_EMOJI} You don't have permission to send codes.", delete_after=5)
    try:
        embed = discord.Embed(title="Match Code", description=f"Your room code vs {member2.name} is:\n```{code}```", color=0x00ff00)
        await member1.send(embed=embed)
        embed2 = discord.Embed(title="Match Code", description=f"Your room code vs {member1.name} is:\n```{code}```", color=0x00ff00)
        await member2.send(embed=embed2)
        await ctx.send(f"{CHECK_EMOJI} Codes sent via DM!", delete_after=3)
        await log_command(ctx.guild.id, ctx.author, "! code1v1", f"1v1 code sent:  {code}")
    except discord.Forbidden:
        await ctx.send(f"{CROSS_EMOJI} Could not send DM to one or more players.  They may have DMs disabled.", delete_after=5)

@bot.command()
async def code2v2(ctx, member1: discord.Member, member2: discord.Member, member3: discord.Member, member4: discord.Member, *, code: str):
    try:
        await ctx.message.delete()
    except:
        pass
    if not has_permission_level_1(ctx.author):
        return await ctx.send(f"{CROSS_EMOJI} You don't have permission to send codes.", delete_after=5)
    try:
        team1_opponents = f"{member3.name} & {member4.name}"
        team2_opponents = f"{member1.name} & {member2.name}"
        embed = discord.Embed(title="Match Code", description=f"Your match code vs {team1_opponents} is:\n```{code}```", color=0x00ff00)
        await member1.send(embed=embed)
        await member2.send(embed=embed)
        embed_b = discord.Embed(title="Match Code", description=f"Your match code vs {team2_opponents} is:\n```{code}```", color=0x00ff00)
        await member3.send(embed=embed_b)
        await member4.send(embed=embed_b)
        await ctx.send(f"{CHECK_EMOJI} Codes sent via DM!", delete_after=3)
        await log_command(ctx.guild.id, ctx.author, "!code2v2", f"2v2 code sent: {code}")
    except discord.Forbidden:
        await ctx.send(f"{CROSS_EMOJI} Could not send DM to one or more players. They may have DMs disabled.", delete_after=5)

@bot.command()
async def invite(ctx, member: discord.Member):
    try:
        await ctx.message. delete()
    except:
        pass
    if member == ctx.author:
        return await ctx.send("❌ You cannot invite yourself.", delete_after=5)
    if member.bot:
        return await ctx.send("❌ You cannot invite bots.", delete_after=5)
    guild_str = str(ctx.guild.id)
    author_team_id = get_team_id(ctx.guild.id, ctx.author.id)
    if author_team_id:  
        return await ctx.send("❌ You are already in a team.   Use `!leave_team` first.", delete_after=5)
    member_team_id = get_team_id(ctx.guild.id, member.id)
    if member_team_id:
        return await ctx.send(f"❌ {member.name} is already in a team.", delete_after=5)
    if guild_str not in team_invitations:
        team_invitations[guild_str] = {}
    member_str = str(member.id)
    if member_str not in team_invitations[guild_str]:
        team_invitations[guild_str][member_str] = []
    if ctx.author.id in team_invitations[guild_str][member_str]:
        return await ctx.send(f"❌ You already sent an invitation to {member.name}.", delete_after=5)
    team_invitations[guild_str][member_str].append(ctx.author.id)
    try:
        invite_view = InviteView(ctx.author, ctx.guild. id)
        await member.send(f"{ctx.author.name} invited you to be their teammate!", view=invite_view)
        await ctx.send(f"✅ Invitation sent to {member.name} via DM!", delete_after=10)
        await log_command(ctx.guild.id, ctx.author, "!invite", f"Sent invitation to {member.name}")
    except discord.Forbidden:
        await ctx.send(f"❌ Cannot send DM to {member.name}. They may have DMs disabled.", delete_after=10)

@bot.command()
async def leave_team(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    team_id = get_team_id(ctx.guild.id, ctx.author.id)
    if not team_id:
        return await ctx.send("❌ You are not in a team.", delete_after=5)
    teammate = get_teammate(ctx.guild.id, ctx.author.id)
    remove_team(ctx.guild.id, team_id)
    if teammate:
        await ctx.send(f"✅ You left the team with {teammate.name}.", delete_after=10)
        await log_command(ctx.guild.id, ctx.author, "!leave_team", f"Left team with {teammate.name}")
    else:
        await ctx. send("✅ You left your team.", delete_after=10)

@bot.command()
async def hosterregist(ctx, max_hosters: int):
    try:
        await ctx.message. delete()
    except:
        pass
    if not has_permission_level_2(ctx.author):
        return await ctx.send(f"{CROSS_EMOJI} You don't have permission to start host registration.", delete_after=5)
    host_registrations['active'] = True
    host_registrations['max_hosters'] = max_hosters
    host_registrations['hosters'] = []
    host_registrations['channel'] = ctx.channel
    embed = discord.Embed(title="🎯 Hoster Registration", description="Register here to become a tournament hoster!", color=0x00ff00)
    embed.add_field(name="Hosters registered:", value="None yet", inline=False)
    embed.add_field(name="Slots:", value=f"0/{max_hosters}", inline=True)
    embed.set_image(url="https://cdn.discordapp.com/attachments/1462029238528905219/1462109996480200765/Screenshot_20260117-174158-7852.png?ex=696cff8b&is=696bae0b&hm=6e4e4d8907016b5fc5652eb01ad3e33eb0624f10593d4730ef7e3c3ab34d4765")
    view = HosterRegistrationView()
    host_registrations['message'] = await ctx.send(embed=embed, view=view)
    await log_command(ctx.guild.id, ctx.author, "!hosterregist", f"Max hosters: {max_hosters}")

@bot.command()
async def start(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    if not has_permission_level_2(ctx.author):
        return await ctx.send(f"{CROSS_EMOJI} You don't have permission to start tournaments.", delete_after=5)
    tournament = get_tournament(ctx.guild.id)
    await log_command(ctx.guild.id, ctx.author, "!start", f"Players: {len(tournament.players)}")
    if tournament.max_players == 0:
        return await ctx.send(f"{CROSS_EMOJI} No tournament has been created yet.", delete_after=5)
    if tournament.active:
        return await ctx.send(f"{CROSS_EMOJI} Tournament already started.", delete_after=5)
    if len(tournament.players) < 2:
        return await ctx.send(f"{CROSS_EMOJI} Not enough players to start tournament (minimum 2 players).", delete_after=5)

    if tournament.mode == "2v2":
        current_teams = len(tournament.players) // 2
        bots_added = 0
        while current_teams % 2 != 0:
            bot1 = FakePlayer("?  ", 100000000000 + tournament.fake_count, placeholder=True)
            tournament.fake_count += 1
            bot2 = FakePlayer("? ", 100000000000 + tournament.fake_count, placeholder=True)
            tournament.fake_count += 1
            tournament.players.extend([bot1, bot2])
            current_teams += 1
            bots_added += 1
        if bots_added > 0:
            await ctx. send(f"Adding {bots_added} bot team(s) to make even bracket.. .", delete_after=5)
        random.shuffle(tournament.players)
        round_pairs = [(tournament.players[i], tournament. players[i+1]) for i in range(0, len(tournament.players), 2)]
        tournament.rounds. append(round_pairs)
        current_round = round_pairs
    else:
        while len(tournament.players) % 2 != 0:
            botp = FakePlayer("? ", 100000000000 + tournament.fake_count, placeholder=True)
            tournament.players.append(botp)
            tournament.fake_count += 1
        random.shuffle(tournament. players)
        round_pairs = [(tournament.players[i], tournament.players[i+1]) for i in range(0, len(tournament.players), 2)]
        tournament.rounds. append(round_pairs)
        current_round = round_pairs

    tournament.active = True
    tournament.results = []

    embed = discord.Embed(
        title=f"{TROPHY_EMOJI} {tournament.title} - Round 1",
        color=0x3498db
    )

    if tournament.mode == "2v2":
        for i, match in enumerate(current_round, 1):
            team_a, team_b = match
            team_a_display = []
            team_b_display = []

            for player in team_a:  
                player_name = get_player_display_name(player, ctx.guild.id)
                team_a_display.append(player_name)

            for player in team_b:  
                player_name = get_player_display_name(player, ctx.guild.id)
                team_b_display.append(player_name)

            team_a_str = " & ".join(team_a_display)
            team_b_str = " & ".join(team_b_display)

            embed.add_field(
                name=f"🏓 Match {i}",
                value=f"**{team_a_str}** {VS_EMOJI} **{team_b_str}**",
                inline=False
            )
    else:
        for i, match in enumerate(current_round, 1):
            a, b = match
            player_a = get_player_display_name(a, ctx.guild.id)
            player_b = get_player_display_name(b, ctx.guild.id)

            embed.add_field(
                name=f"🏓 Match {i}",
                value=f"**{player_a}** {VS_EMOJI} **{player_b}**",
                inline=False
            )

    embed.set_image(url="https://cdn.discordapp.com/attachments/1462029238528905219/1462109996480200765/Screenshot_20260117-174158-7852.png?ex=696cff8b&is=696bae0b&hm=6e4e4d8907016b5fc5652eb01ad3e33eb0624f10593d4730ef7e3c3ab34d4765")
    winners_view = WinnersView(ctx.guild.id)
    tournament.message = await ctx.send(embed=embed, view=winners_view)

@bot.command()
async def restart(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ You don't have permission to restart tournaments.", delete_after=5)
    tournament = get_tournament(ctx.guild.id)
    if tournament.max_players == 0:
        return await ctx.send("❌ No tournament has been created yet.", delete_after=5)
    tournament.__init__()
    await ctx.send("✅ Tournament has been restarted!  You can create a new tournament now.", delete_after=10)
    await log_command(ctx. guild.id, ctx.author, "!restart", "Tournament reset")

def _get_avatar_url_from_obj(obj):
    try:
        if isinstance(obj, FakePlayer):
            return None
        if isinstance(obj, list) and len(obj) > 0:
            first = obj[0]
            if hasattr(first, "display_avatar"):
                return first.display_avatar. url
        if hasattr(obj, "display_avatar"):
            return obj.display_avatar.url
    except Exception:
        return None
    return None

@bot.command()
async def winner(ctx, member: discord.Member):
    try:
        await ctx.message.delete()
    except:
        pass
    if not has_permission_level_1(ctx.author):
        return await ctx.send(f"{CROSS_EMOJI} You don't have permission to set winners.", delete_after=5)
    tournament = get_tournament(ctx.guild.id)
    if not tournament.active:
        return await ctx.send(f"{CROSS_EMOJI} No active tournament.", delete_after=5)

    current_round = tournament.rounds[-1]
    match_found = False
    eliminated_players = []
    match_index = -1
    winner_team = None
    winner_name = ""

    if tournament.mode == "2v2":  
        member_team_id = get_team_id(ctx.guild.id, member.id)
        if not member_team_id:
            return await ctx.send("❌ This player is not in a team.", delete_after=5)

        for i, match in enumerate(current_round):
            team_a, team_b = match
            if member in team_a:
                winner_team = team_a
                tournament.results.append(team_a)
                eliminated_players.extend(team_b)
                match_found = True
                match_index = i
                break
            elif member in team_b:
                winner_team = team_b
                tournament.results. append(team_b)
                eliminated_players.extend(team_a)
                match_found = True
                match_index = i
                break

        if match_found:
            winner_name = get_team_display_name(ctx.guild.id, winner_team)
            round_number = len(tournament.rounds)
            match_key = f"round_{round_number}_match_{match_index + 1}"
            tournament.match_winners[match_key] = winner_team
    else: 
        for i, match in enumerate(current_round):
            a, b = match
            if member == a or member == b:
                tournament.results.append(member)
                eliminated_players.extend([a if member == b else b])
                match_found = True
                match_index = i
                break

        if match_found:
            winner_name = get_player_display_name(member, ctx.guild.id)
            round_number = len(tournament.rounds)
            match_key = f"round_{round_number}_match_{match_index + 1}"
            tournament.match_winners[match_key] = member

    if not match_found:
        return await ctx.send("❌ This player/team is not in the current round.", delete_after=5)

    tournament.eliminated. extend(eliminated_players)

    if len(tournament.results) == len(current_round):
        if len(tournament.results) == 1:
            winner_data = tournament.results[0]
            all_eliminated = tournament.eliminated

            def _name_for(obj, bold=True):
                if isinstance(obj, list):
                    return get_team_display_name(ctx.guild.id, obj)
                if isinstance(obj, FakePlayer):
                    return "Bot"
                return get_player_display_name(obj, ctx.guild.id, bold=bold)

            placements = []
            winner_data = tournament.results[0]
            if not (isinstance(winner_data, FakePlayer) or (isinstance(winner_data, list) and any(isinstance(p, FakePlayer) for p in winner_data))):
                placements.append((1, winner_data))
            
            real_eliminated = []
            for p in tournament.eliminated:
                if isinstance(p, list):
                    if not any(isinstance(m, FakePlayer) for m in p):
                        real_eliminated.append(p)
                elif not isinstance(p, FakePlayer):
                    real_eliminated.append(p)

            for i, p in enumerate(reversed(real_eliminated)):
                if len(placements) < 4:
                    placements.append((len(placements) + 1, p))

            p1 = placements[0][1] if len(placements) >= 1 else None
            p2 = placements[1][1] if len(placements) >= 2 else None
            p3 = placements[2][1] if len(placements) >= 3 else None
            p4 = placements[3][1] if len(placements) >= 4 else None

            embed = discord.Embed(
                title=f"{TROPHY_EMOJI} Tournament Winners!  {TROPHY_EMOJI}",
                description=f"Congratulations to **{_name_for(p1, bold=False)}** for winning the **{tournament.title}** tournament!  🎉",
                color=0xffd700
            )

            rankings_text = ""
            rankings_text += f"🥇 {_name_for(p1) if p1 else '—'}\n"
            rankings_text += f"🥈 {_name_for(p2) if p2 else '—'}\n"
            rankings_text += f"🥉 {_name_for(p3) if p3 else '—'}\n"
            rankings_text += f"🏅 {_name_for(p4) if p4 else '—'}\n"
            embed.add_field(name=f"{TROPHY_EMOJI} Final Rankings", value=rankings_text, inline=False)

            prizes_text = ""
            prizes_text += f"🥇 1st: {tournament.prize_1st or '—'}\n"
            prizes_text += f"🥈 2nd: {tournament.prize_2nd or '—'}\n"
            prizes_text += f"🥉 3rd: {tournament.prize_3rd or '—'}\n"
            prizes_text += f"🏅 4th: {tournament.prize_4th or '—'}\n"
            embed.add_field(name="<:Crown:1462065099622842450> Prizes", value=prizes_text, inline=False)

            winner_avatar = _get_avatar_url_from_obj(p1)
            if winner_avatar:
                try:
                    embed.set_thumbnail(url=winner_avatar)
                except Exception:
                    pass

            await ctx.send(embed=embed)
            tournament.__init__()
        else:
            next_round_winners = tournament.results. copy()

            while len(next_round_winners) % 2 != 0:
                bot = FakePlayer("? ", 100000000000 + tournament.fake_count)
                next_round_winners.append(bot)
                tournament.fake_count += 1

            next_round_pairs = [(next_round_winners[i], next_round_winners[i+1]) for i in range(0, len(next_round_winners), 2)]
            tournament.rounds.append(next_round_pairs)
            tournament.results = []

            round_num = len(tournament.rounds)
            embed = discord.Embed(title=f"{TROPHY_EMOJI} {tournament.title} - Round {round_num}", color=0x3498db)

            for i, match in enumerate(next_round_pairs, 1):
                a, b = match
                if tournament.mode == "2v2":  
                    a_display = get_team_display_name(ctx.guild.id, a)
                    b_display = get_team_display_name(ctx. guild.id, b)
                else:
                    a_display = get_player_display_name(a, ctx.guild.id)
                    b_display = get_player_display_name(b, ctx.guild.id)

                embed.add_field(
                    name=f"🏓 Match {i}",
                    value=f"**{a_display}** {VS_EMOJI} **{b_display}**",
                    inline=False
                )

            embed.set_image(url="https://cdn.discordapp.com/attachments/1462029238528905219/1462109996480200765/Screenshot_20260117-174158-7852.png?ex=696cff8b&is=696bae0b&hm=6e4e4d8907016b5fc5652eb01ad3e33eb0624f10593d4730ef7e3c3ab34d4765")
            winners_view = WinnersView(ctx.guild.id)