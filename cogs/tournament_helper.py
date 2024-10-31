import discord
from discord.ui import View, Button
from discord.ext import commands
from discord.ext.commands import BucketType
from data.game_data import BRACKET, TEAMS, MAPS
import random
import asyncio
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from data.globals import active_series

class TournamentHelper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bracket = BRACKET
        self.rounds = ["Quarterfinals", "Semifinals", "Finals"]
        self.teams = TEAMS
                                        # my testing channel | drafting channel
        self.ALLOWED_CHANNELS_CAPTAINS = []

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from the bot itself to prevent loops
        if message.author == self.bot.user:
            return

        if message.content.startswith(self.bot.command_prefix):
            return  # Skip the listener if it's a command

        # Check if "hello snipey" is in the message content
        if "hello snipey" in message.content.lower():
            await message.channel.send(f"Hi {message.author.mention}!")

        if "mvponaloss" in message.content.lower():
            await message.channel.send("FeelsAbzeerMan")

        if "thank you snipey" in message.content.lower():
            await message.channel.send(f"You're welcome {message.author.mention}!")
        
        # Allow the bot to process other commands
        await self.bot.process_commands(message)  

    @commands.command()
    async def help(self,ctx):
        embed = discord.Embed(
            title="Tournament Commands",
            description="Here are the available commands and their usage:",
            color=discord.Color.red()
        )
        embed.add_field(name="!ban (captains only)", value="Begins the map ban phase.  Use `!ban @<enemy captain>`.", inline=False)
        embed.add_field(name="!bracket", value="Displays current bracket.", inline=False)
        embed.add_field(name="!flip (captains only)", value="Performs a coin toss to determine starting position for ban phase.", inline=False)
        embed.add_field(name="!maps", value="Displays playable maps.", inline=False)
        embed.add_field(name="!picks", value="Displays the heroes any team has picked in the Raviment, use format `!picks <team abbrev>`.", inline=False)
        embed.add_field(name="!report (captains only)", value="Used at the end of a series to record the score.\nUse format `!report <team1 abbrev> 0-0 <team2-abbrev>`", inline=False)
        embed.add_field(name="!teams", value="Displays the teams and abbreviations.", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def modhelp(self,ctx):
        embed = discord.Embed(
            title="Tournament Commands",
            description="Here are the available commands and their usage:",
            color=discord.Color.red()
        )
        embed.add_field(name="!closeseries", value="Used at the end of a series.  Use format `!closeseries <#>`.", inline=False)
        embed.add_field(name="!match", value="Used to record team comps. After opening a series, use `!match <#>` to record picks.", inline=False)
        embed.add_field(name="!series", value="Opens a series between two teams for tracking. Use format `!series <#> <team1 team2>`. Use team abbreviations in place of team names.", inline=False)
        await ctx.send(embed=embed)

    def create_embed(self, round_name):
        embed = discord.Embed(title=f"{round_name} Bracket", color=discord.Color.red())
        round_data = self.bracket[round_name]

        for series_name, series_info in round_data.items():
            team1_abbr = series_info["Team 1"]
            team2_abbr = series_info["Team 2"]
            
            team1_full_name = self.teams.get(team1_abbr, team1_abbr) # Get full names for display purposes
            team2_full_name = self.teams.get(team2_abbr, team2_abbr)
            team1_wins = series_info["Team 1 Wins"]
            team2_wins = series_info["Team 2 Wins"]
            series_winner = series_info["Series Winner"] or "TBD"

            embed.add_field(
                name=f"{series_name} - {team1_full_name} -vs- {team2_full_name}",
                value=f"{team1_abbr} score: {team1_wins} \n{team2_abbr} score: {team2_wins}\n**Series Winner:** {series_winner}",
                inline=False
            )
        embed.set_footer(text="- - - Bracket updates after every series is over and reported - - -")
        return embed

    @commands.command()
    @commands.cooldown(rate=1, per=60, type=BucketType.guild)  # 1 use every 60 seconds for the entire server
    async def bracket(self, ctx):
        """Command to start the bracket navigation."""
        view = BracketView(self, ctx)
        await view.send_initial_message()

class BanPhase(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.maps = MAPS
        self.sheet = self.auth_google_sheets()
        self.worksheet = self.sheet
                                        # my testing channel | drafting channel 
        self.ALLOWED_CHANNELS_CAPTAINS = [1290751062256648212, 1300568326606422086]

    def auth_google_sheets(self):
        # Scope for sheets & drive
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Load credentials from .json file
        creds = ServiceAccountCredentials.from_json_keyfile_name("C:\\Users\\LadyD\\AppData\\Local\\Programs\\Python\\Python312\\Projects\\HotsCalc\\snipey-bfcd3543a260.json", scope)
        client = gspread.authorize(creds)  # Authorize client to interact with sheets
        sheet = client.open("Snipey data")  # Open specific sheet
        worksheet = sheet.get_worksheet(2)  # Access the third worksheet
        return worksheet

    @commands.command()
    async def maps(self, ctx: commands.Context):
        embed = discord.Embed(
            title="3k Raviment Map Pool",
            color=discord.Color.red()
        )
        embed.add_field(name="", value='\n'.join(['- ' + map_name for map_name in self.maps]), inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role("Captains", "Ravinar", "Ellixya")
    async def flip(self, ctx: commands.Context):
        if ctx.channel.id not in self.ALLOWED_CHANNELS_CAPTAINS:
            await ctx.send(f"{ctx.author.mention}, this command can only be used in the `#-drafting-and-match-reporting` channel.")
            return   
        result = random.choice(["map ban", "first pick"])
        await ctx.send(f"{ctx.author.mention}, your team gets: {result}")

    @commands.command() 
    @commands.has_any_role("Captains", "Ravinar", "Ellixya")
    async def ban(self, ctx: commands.Context, user: discord.Member):
        global TEAMS
        if ctx.channel.id not in self.ALLOWED_CHANNELS_CAPTAINS:
            await ctx.send(f"{ctx.author.mention}, this command can only be used in the `#-drafting-and-match-reporting` channel.")
            return   
        remaining_maps = self.maps.copy()  # Create a copy of the maps list
        rounds = 2
        users = [ctx.author, user]  # User 1 and User 2
        current_user_index = 0  # Start with User 1
        banned_maps = {ctx.author.id: [], user.id: []}  # Initialize banned_maps for both users

        # Check team roles for both users
        team_roles = {user.id: self.get_user_team(user) for user in users}

        for round_number in range(1, rounds + 1):
            for _ in range(2):  # Each user gets two turns per round
                current_user = users[current_user_index]

                while True:  # Loop until the user provides valid input
                    await ctx.send(f"{current_user.mention}, please name a map to ban:\nRemaining maps: {', '.join(remaining_maps)}")

                    def check(msg):
                        return msg.author == current_user and msg.channel == ctx.channel

                    try:
                        user_input = await self.bot.wait_for('message', check=check, timeout=60)  # 60 seconds to respond
                        if user_input.content.lower() == "cancel":
                            await ctx.send("Input canceled.")
                            return    
                        items_to_remove = [item.strip() for item in user_input.content.split(',') if item.strip()]

                        # To track matched items
                        matched_items = []

                        # Check each item for matches
                        for item in items_to_remove:
                            # Match items by first word (case insensitive)
                            matched = [map_name for map_name in remaining_maps if map_name.lower().startswith(item.lower())]
                            
                            if matched:
                                matched_items.extend(matched)  # Add matched items to the list
                            else:
                                await ctx.send(f"{item} did not match any remaining maps. Please try again.")
                                break  # Exit the current user's input loop if there is an invalid input

                        # If there are valid matched items, remove them
                        if matched_items:
                            for map_name in matched_items:
                                remaining_maps.remove(map_name)  # Remove matched item
                                banned_maps[current_user.id].extend(matched_items)  # Add to the user's banned maps
                                await ctx.send(f"{map_name} has been banned.")
                            break  # Break the while loop if the input was valid

                    except asyncio.TimeoutError:
                        await ctx.send(f"{current_user.mention}, you took too long to respond! Ending the ban phase.")
                        return  # Exit the command if the user times out

                current_user_index = (current_user_index + 1) % 2  # Switch to the next user

        # Display remaining maps after all rounds
        if remaining_maps:
            embed = discord.Embed(
                title="Playable maps for this series",
                color=discord.Color.red()
            )
            embed.add_field(name="", value='\n'.join(['- ' + map_name for map_name in remaining_maps]), inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("No maps remain.")

        # Save banned maps to Google Sheets based on team roles
        await self.save_banned_maps_to_sheets(banned_maps, team_roles, ctx, user)

        banned_maps = {ctx.author.id: [], user.id: []}  # Clear the dict after round ends

    def get_user_team(self, user: discord.Member):
        global TEAMS
        """Get the team abbreviation based on the user's roles."""
        for role in user.roles:
            for abbreviation, role_name in TEAMS.items():
                if role.name == role_name:
                    return abbreviation  # Return the abbreviation of the team
        return None  # Return None if no team found

    async def save_banned_maps_to_sheets(self, banned_maps, team_roles, ctx, user):
        global active_series
        """Save banned maps to the respective Google Sheets fields."""
        team1 = team_roles[ctx.author.id]
        team2 = team_roles[user.id]

        series_key = (team1, team2)
        reverse_series_key = (team2, team1)
        is_reverse = False
        print(f"Checking series keys: {series_key} or {reverse_series_key}")  # Debug statement
        # Check if the series keys are in active_series
        if series_key in active_series:
            series_id = active_series[series_key]['series_id']
            print(f"Found series ID for key {series_key}: {series_id}")
        elif reverse_series_key in active_series:
            series_id = active_series[reverse_series_key]['series_id']
            print(f"Found series ID for reverse key {reverse_series_key}: {series_id}")
            is_reverse = True
        else:
            print(f"No matching series found for keys: {series_key} or {reverse_series_key}")
            return  # Exit if no matching series

        try:
            for idx, row in enumerate(self.worksheet.get_all_records(), start=2):  # Start from 2 to skip headers
                if row['Series ID'] == series_id:  # Look for the specific series ID
                    print(f"Matched series ID: {row['Series ID']}")
                    # Check if the user ID exists in team_roles and store their banned maps
                    user_bans = banned_maps.get(ctx.author.id, [])
                    opponent_bans = banned_maps.get(user.id, [])
                    # Determine the columns based on whether the teams are reversed
                    if is_reverse:
                        await asyncio.to_thread(self.worksheet.update_cell, idx, 10, ', '.join(opponent_bans).strip(", "))  # Update column for Team 1 Bans
                        await asyncio.to_thread(self.worksheet.update_cell, idx, 11, ', '.join(user_bans).strip(", "))  # Update column for Team 2 Bans
                        print(f"Updated Team 1 Bans: {opponent_bans}.\nUpdated Team 2 Bans: {user_bans} on Sheets.")  # Debug output

                    else:
                        await asyncio.to_thread(self.worksheet.update_cell, idx, 10, ', '.join(user_bans).strip(", "))
                        await asyncio.to_thread(self.worksheet.update_cell, idx, 11, ', '.join(opponent_bans).strip(", ")) # Update column for Team 2 Bans
                        print(f"Updated Team 1 Bans: {opponent_bans}.\nUpdated Team 2 Bans: {user_bans} on Sheets.")  # Debug output

                    break  # Break after finding the correct row
        except Exception as e:
            print(f"Error updating Google Sheets: {e}")  # Log any errors

class MatchReporting(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
        self.sheet = self.auth_google_sheets()
        self.worksheet = self.sheet
                                        # my testing channel | drafting channel 
        self.ALLOWED_CHANNELS_CAPTAINS = [1290751062256648212, 1300568326606422086]
        self.load_bracket_state()

    @commands.Cog.listener() # Command to return an error if the user doesn't have required roles for command.
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send(f"{ctx.author.mention}, you don't have permission to use this command, this is a Captains-only command.")

    def auth_google_sheets(self):
        # Scope for sheets & drive
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Load credentials from .json file
        creds = ServiceAccountCredentials.from_json_keyfile_name("C:\\Users\\LadyD\\AppData\\Local\\Programs\\Python\\Python312\\Projects\\HotsCalc\\snipey-bfcd3543a260.json", scope)
        client = gspread.authorize(creds)  # Authorize client to interact with sheets
        sheet = client.open("Snipey data")  # Open specific sheet
        worksheet = sheet.get_worksheet(2)  # Access the third worksheet
        return worksheet

    def save_bracket_state(self):
        global BRACKET
        """Saves the current bracket state to Google Sheets."""
        # Iterate through each round and series to save the full bracket snapshot
        for round_name, series in BRACKET.items():
            for series_id, details in series.items():
                # Prepare the row data for the series
                row_data = [
                    round_name,                            # Round
                    "Completed" if details["Series Winner"] != "TBD" else "Pending",  # Round Status
                    series_id,                             # Series ID
                    details["Team 1 Wins"],                # Wins by Team 1
                    details["Team 2 Wins"],                # Wins by Team 2
                    details["Series Winner"] or ""         # Series Winner
                ]

                # Find if the series ID already exists in the sheet to update; otherwise, append a new row
                matching_cells = self.worksheet.findall(str(series_id))
                
                # Validate that matching_cells has found the correct series row
                if matching_cells:
                    for cell in matching_cells:
                        row = cell.row
                        # Validate row to ensure it's the correct Series ID before updating
                        cell_series_id = self.worksheet.cell(row, 5).value  # Assumes 'Series ID' is in column E (5)
                        if cell_series_id == str(series_id):  # Exact match with Series ID
                            # Update the existing row in the Google Sheet
                            self.worksheet.update(f'C{row}:H{row}', [row_data])
                            print(f"Updated row for Series ID {series_id}: {row_data}")  # Debug confirmation
                            break
                    else:
                        # If no match is found, add a new row for the series
                        self.worksheet.append_row(row_data)
                        print(f"Appended new row for Series ID {series_id}: {row_data}")
                else:
                    # No match found at all, append a new row for the series
                    self.worksheet.append_row(row_data)
                    print(f"Appended new row for Series ID {series_id}: {row_data}")

        print("Bracket state saved to Google Sheets.")

    def load_bracket_state(self):
        try:
            data = self.worksheet.get_all_records()

            for entry in data:
                round_name = entry.get("Round")
                series_id = str(entry.get("Series ID"))  # Ensure it's a string
                team1 = entry.get("Team 1")
                team2 = entry.get("Team 2")
                team1_wins = entry.get("Team 1 Wins", 0)  # Default to 0 if missing
                team2_wins = entry.get("Team 2 Wins", 0)  # Default to 0 if missing
                series_winner = entry.get("Series Winner") or None

                # Check if the round and series ID exist in the BRACKET
                if round_name in BRACKET and series_id in BRACKET[round_name]:
                    # Update the BRACKET with the values from the Google Sheets
                    BRACKET[round_name][series_id].update({
                        "Team 1": team1,   # Update Team 1
                        "Team 2": team2,   # Update Team 2
                        "Team 1 Wins": team1_wins,
                        "Team 2 Wins": team2_wins,
                        "Series Winner": series_winner or None
                    })
                else:
                    print(f"Warning: {round_name} - Series ID {series_id} not found in BRACKET.")

            print("Bracket state loaded from Google Sheets.")
        except Exception as e:
            print(f"Error loading bracket state: {e}")

    @commands.command()
    @commands.has_any_role("Captains", "Ravinar", "Ellixya")
    async def report(self, ctx, team1: str, score: str, team2: str):
        global TEAMS
        global active_series
        global BRACKET
        if ctx.channel.id not in self.ALLOWED_CHANNELS_CAPTAINS:
            await ctx.send(f"{ctx.author.mention}, this command can only be used in the `#-drafting-and-match-reporting` channel.")
            return   
        self.load_bracket_state()
        print(f"TOP ACTIVE {active_series}")
        team1 = team1.upper()
        team2 = team2.upper()
        print("Command invoked")  # Debug statement
        # Split the score into two parts
        try:
            score1, score2 = map(int, score.split('-'))
            print(f"Scores received: {score1} - {score2}")  # Debug statement
        except ValueError:
            await ctx.send("Invalid score format. Use 'team1 score1-score2 team2'.")
            return

        # Check if the series is active using upper() for case insensitivity
        series_key = (team1, team2)
        reverse_series_key = (team2, team1)
        
        print(f"Checking series keys: {series_key} or {reverse_series_key}")  # Debug statement
        if series_key not in active_series and reverse_series_key not in active_series:
            print(f"ACTIVE SERIES {active_series}")
            await ctx.send("No active series found between these teams.")
            return
        
        # Determine the active series
        current_active_series = active_series.get(series_key) or active_series.get(reverse_series_key)
        print(f"Active series found: {current_active_series}")  # Debug statement

        if current_active_series:
            # Retrieve bracket details
            for round_name, series in BRACKET.items():
                for series_name, details in series.items():
                    if ((details["Team 1"].upper() == current_active_series["team1"].upper() and
                        details["Team 2"].upper() == current_active_series["team2"].upper()) or
                        (details["Team 1"].upper() == current_active_series["team2"].upper() and
                        details["Team 2"].upper() == current_active_series["team1"].upper())):
                        
                        # Check if there's an existing score
                        if details["Team 1 Wins"] > 0 or details["Team 2 Wins"] > 0:
                            await ctx.send("This match has already been reported. No further updates allowed. Please reach out to a mod if there was an error.")
                            print(f"Score already exists for series {series_name}: {details}")
                            return  # Exit if scores are already recorded
                        
                        # Determine if we need to reverse the scores
                        if reverse_series_key in active_series:
                            # If we are using the reverse key, flip the scores
                            details["Team 1 Wins"] += score2  # score2 goes to Team 1
                            details["Team 2 Wins"] += score1  # score1 goes to Team 2
                            winner = team2 if score2 > score1 else team1  # Determine winner based on new score assignment
                        else:
                            # Normal assignment
                            details["Team 1 Wins"] += score1  # score1 goes to Team 1
                            details["Team 2 Wins"] += score2  # score2 goes to Team 2
                            winner = team1 if score1 > score2 else team2  # Determine winner based on score assignment

                        # Ensure there is a valid winner
                        if score1 == score2:
                            await ctx.send("The match result cannot be a tie. Please report a valid score.")
                            return
                        
                        details["Series Winner"] = winner  # Directly assign the series winner

                        full_name = TEAMS.get(winner, winner)  # Use the winner's full name
                        await ctx.send(f"Match reported as {team1} {score1}-{score2} {team2}.\nThe winner is: **{full_name}**!")
                        
                        print(f"Bracket updated: {details}")  # Debug statement
                        self.save_bracket_state()  # Save the updated bracket
                        self.load_bracket_state()
                        return  # Exit after updating

        print("No matching series found in the bracket to update.")  # Debug statement

class BracketView(discord.ui.View):
    def __init__(self, cog, ctx, current_round=0, timeout=180):
        super().__init__(timeout=timeout)  # Set a longer timeout if needed
        self.cog = cog
        self.ctx = ctx
        self.current_round = current_round
        self.rounds = self.cog.rounds  # ["Quarterfinals", "Semifinals", "Finals"]
        self.message = None  # This will store the message reference

    async def send_initial_message(self):
        # Send the initial message with the bracket embed
        embed = self.cog.create_embed(self.rounds[self.current_round])
        self.message = await self.ctx.send(embed=embed, view=self)

    async def update_message(self):
        # Update the embed in the existing message
        embed = self.cog.create_embed(self.rounds[self.current_round])
        if self.message:
            await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, custom_id="previous")
    async def previous_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.current_round > 0:
            self.current_round -= 1
            await self.update_message()
        await interaction.response.defer()  # Acknowledge interaction without sending a response

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, custom_id="next")
    async def next_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.current_round < len(self.rounds) - 1:
            self.current_round += 1
            await self.update_message()
        await interaction.response.defer()  # Acknowledge interaction without sending a response

async def setup(bot):
    await bot.add_cog(MatchReporting(bot))
    await bot.add_cog(TournamentHelper(bot))
    await bot.add_cog(BanPhase(bot))
