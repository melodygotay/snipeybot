import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
from data.game_data import TEAMS, HEROES, BRACKET
import re
from data.globals import active_series

class HeroMatch:
    def __init__(self, HEROES):
        self.heroes = HEROES

    def normalize(self, hero_name):
        """Normalize hero names for comparison."""
        # Replace spaces with hyphens and remove punctuation, then lower the case
        normalized = re.sub(r'\s+', '-', hero_name)  # Replace spaces with hyphens
        normalized = re.sub(r'[^\w-]', '', normalized)  # Remove punctuation except for hyphens
        return normalized.lower().strip()  # Lowercase and strip spaces

    def match_heroes(self, input_string):
        # Split the input into hero names
        hero_names = [hero.strip() for hero in input_string.split(',')]
        matched_heroes = []
        unmatched_heroes = []

        # Normalize the heroes from the dictionary for comparison
        normalized_heroes = {
            self.normalize(h): h for role, hs in self.heroes.items() for h in hs
        }

        for hero in hero_names:
            # Normalize the hero name for comparison
            normalized_hero = self.normalize(hero)
            print(f"Checking input: '{normalized_hero}'")  # Debug output
            
            # Try to find the normalized hero in the pre-normalized heroes dictionary
            if normalized_hero in normalized_heroes:
                matched_heroes.append(normalized_heroes[normalized_hero])
            else:
                matched_heroes.append("Invalid")

            if normalized_hero not in normalized_heroes:
                unmatched_heroes.append(hero)
            else:
                unmatched_heroes.append("")

        return matched_heroes, unmatched_heroes

# Constants for statuses
ACTIVE_STATUS = 'Active'
CLOSED_STATUS = 'Closed'
EMPTY = ""

class CompTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sheet = self.auth_google_sheets()
        self.worksheet = self.sheet
        self.teams = TEAMS
        self.heroes = HEROES
        self.hero_matcher = HeroMatch(HEROES)  # Initialize HeroMatch with the HEROES dictionary

    @commands.command()
    async def teams(self, ctx: commands.Context):
        embed = discord.Embed(
            title="3k Raviment Teams",
            description="Use these abbreviations when starting new series'.",
            color=discord.Color.red()
        )
        embed.add_field(name="", value="**`BCH`:**  Barley's Chewies", inline=False)
        embed.add_field(name="", value="**`TMT`:**  Team Two", inline=False)
        embed.add_field(name="", value='**`MRU`:**  Memes "R" Us', inline=False)
        embed.add_field(name="", value="**`CTZ`:**  Confused Time Zoners", inline=False)
        embed.add_field(name="", value="**`FLO`:**  Floccinaucinihilipilification", inline=False)
        embed.add_field(name="", value="**`MVP`:**  MVP on a Loss FeelsAbzeerMan", inline=False)
        embed.add_field(name="", value="**`PBR`:**  Peanut Butter Randos", inline=False)
        embed.add_field(name="", value="**`DOH`:**  Disciples of the Highlord", inline=False)
        await ctx.send(embed=embed)

    def auth_google_sheets(self):
        # Scope for sheets & drive
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Load credentials from .json file
        creds = ServiceAccountCredentials.from_json_keyfile_name("C:\\Users\\LadyD\\AppData\\Local\\Programs\\Python\\Python312\\Projects\\HotsCalc\\snipey-bfcd3543a260.json", scope)
        client = gspread.authorize(creds)  # Authorize client to interact with sheets
        sheet = client.open("Snipey data")  # Open specific sheet
        worksheet = sheet.get_worksheet(1)  # Access the second worksheet
        return worksheet

    def get_active_series(self, team1, team2):
        global active_series
        # Search for active series with the given team names in the Google Sheet
        records = self.worksheet.get_all_records()
        for row in records:
            if (row['Team 1 Name'] == team1 or row['Team 2 Name'] == team1) and \
            (row['Team 1 Name'] == team2 or row['Team 2 Name'] == team2) and \
            row['Series Status'] == ACTIVE_STATUS and row['Match Status'] == ACTIVE_STATUS:
                active_series[(team1, team2)] = {
                    'series_id': row['Series ID'],
                    'current_match_id': row['Match ID'],  # Initialize match_id if needed
                    'team1': team1,
                    'team2': team2
                }
                return row['Series ID'], row['Match ID']
        return None, None

    def start_new_series(self, series_id, team1, team2):
        global active_series
        # Store the series ID as the active one
        existing_id, _ = self.get_active_series(team1, team2)
        if not existing_id:
            active_series[(team1, team2)] = {
                'series_id': series_id,
                'current_match_id': 0,  # Initialize match_id if needed
                'team1': team1,
                'team2': team2
            }
       
        print(f"Series {series_id} between {team1} and {team2} started.")
    
    def start_new_match(self, team1, team2, match_id):
        global active_series
        print(f"Starting new match for {team1} vs {team2} with match ID {match_id}")
        
        # Check if an active series exists directly
        series_info = active_series.get((team1, team2))
        if series_info is None:
            raise ValueError("No active series. Please start a new series first by using !series.")

        # Extract series ID and current match ID
        series_id = series_info['series_id']
        current_match_id = series_info['current_match_id']

        # Check if match ID already exists in the worksheet
        records = self.worksheet.get_all_records()
        match_exists = any(row['Match ID'] == match_id and row['Series ID'] == series_id for row in records)

        if match_exists:
            print(f"Match {match_id} in Series ID {series_id} already exists.")
            return current_match_id  # Return existing match ID if found

        # If no match ID exists, append a new row with match details
        self.worksheet.append_row([
            team1.upper(), team2.upper(), series_id, match_id, ACTIVE_STATUS, ACTIVE_STATUS
        ])
        print(f"New match started for Series ID {series_id} with Match ID {match_id}, Teams: {team1} vs {team2}")
        series_info['current_match_id'] = match_id 
        return match_id

    def can_pick_hero(self, series_id, team_name, hero_name):
        # Find all records for the active series
        records = self.worksheet.get_all_records()

        # Check if the hero has already been picked by this team in this series
        for row in records:
            if row['Series ID'] == series_id:
                if row['Team 1 Name'] == team_name:
                    # Assuming heroes for Team 1 are stored starting from column 6 (index 5)
                    if hero_name in [row[col] for col in row.keys() if col.startswith('Team 1 Hero')]:
                        return False  # Hero has already been picked by this team

                if row['Team 2 Name'] == team_name:
                    # Assuming heroes for Team 2 are stored starting from column 11 (index 10)
                    if hero_name in [row[col] for col in row.keys() if col.startswith('Team 2 Hero')]:
                        return False  # Hero has already been picked by this team
        return True

    def update_player_pick(self, series_id, match_id, team_name, player_index, hero_name):
        records = self.worksheet.get_all_records()
        # If hero is not picked yet, proceed to update
        for index, row in enumerate(records):
            if row['Series ID'] == series_id and row['Match ID'] == match_id:
                if team_name == row['Team 1 Name']:
                    column_index = 7 + player_index  # Assuming hero picks for Team 1 start from column 7
                else:
                    column_index = 12 + player_index  # Assuming hero picks for Team 2 start after Team 1

                self.worksheet.update_cell(index + 2, column_index, hero_name)  # Update the cell with hero_name
                return True  # Successfully updated

        return False  # No match found for the update

    def clear_team_picks(self, series_id, match_id):
        # Fetch all records to find the target row
        records = self.worksheet.get_all_records()
        target_row = None

        for index, row in enumerate(records):
            # Find the row that matches both series and match IDs
            if row['Series ID'] == series_id and row['Match ID'] == match_id:
                target_row = index + 2  # Adjust for header row
                break

        if target_row:
            # Clear columns 7 through 16 for the identified row
            for col in range(7, 17):
                self.worksheet.update_cell(target_row, col, "")
            
            print(f"Cleared picks for series {series_id}, match {match_id} in row {target_row}.")
            return True  # Indicate success
        else:
            print(f"No matching row found for series {series_id} and match {match_id}.")
            return False  # Indicate failure

    @commands.command()
    async def series(self, ctx, series_id: int, team1: str, team2: str):
        global active_series
        global BRACKET
        
        # Normalize team names to uppercase for consistency
        team1 = team1.upper()
        team2 = team2.upper()
        
        # Check if both teams are valid
        if team1 not in self.teams or team2 not in self.teams:
            await ctx.send(f"Invalid teams: '{team1}' and/or '{team2}'. Please use the following abbreviations: {', '.join(self.teams.keys())}")
            return

        # Retrieve expected teams from BRACKET
        expected_teams = None
        for round_name, series in BRACKET.items():
            if str(series_id) in series:
                expected_teams = series[str(series_id)]
                break

        if expected_teams is None:
            await ctx.send(f"No series found with ID {series_id}.")
            return

        bracket_team1 = expected_teams['Team 1'].upper() # Retrieve expected teams from the bracket

        if team1 != bracket_team1: # Check if team1 matches the bracket's Team 1
            team1, team2 = team2, team1 # If not, swap team1 and team2

        # Check if the series already exists in the active series
        if (team1, team2) in active_series:
            await ctx.send(f"A series between **{team1}** and **{team2}** is already active.")
            return
        
        if len(active_series) > 0:
            previous_series_key = next(iter(active_series))  # In case there's more than one series
            del active_series[previous_series_key]  # Remove the previous active series

        existing_records = self.worksheet.get_all_records()
        series_exists = False
        latest_match_id = 0

        for row in existing_records:
            if (row['Series ID'] == series_id and 
                row['Team 1 Name'].upper() == team1 and 
                row['Team 2 Name'].upper() == team2):
                series_exists = True
                if row['Match ID'] > latest_match_id:
                    latest_match_id = row['Match ID']

        if series_exists:  # If series exists, make it the active series
            active_series[(team1, team2)] = {
                'series_id': series_id,
                'current_match_id': latest_match_id,  # Initialize match_id if needed
                'team1': team1,
                'team2': team2
            }
            await ctx.send(f"Series {series_id} between **{team1}** and **{team2}** is now active.")
            print(f"Active Series: {active_series}")  # Debugging line
            return

        # If the series does not exist, create a new series
        self.start_new_series(series_id, team1, team2)

        print(f"Active Series: {active_series}")  # Debugging line
        full_team1 = self.teams.get(team1, team1)
        full_team2 = self.teams.get(team2, team2)
        await ctx.send(f"Started new series between **{full_team1}** and **{full_team2}**.")

    @commands.command()
    async def match(self, ctx, match_id: int):
        global active_series
        series_info = None
        previous_match_id = match_id - 1

            # For match_id 1, we don't need to check for previous matches
        if match_id == 1:
            # Ensure there's an active series before starting match 1
            if not active_series:
                await ctx.send("No active series exists. Please start a series first.")
                return
            
            # Get the first active series (you may want to refine this if needed)
            (team1, team2), info = next(iter(active_series.items()))
            series_id = info['series_id']
            
            # Set series_info with the active series
            series_info = info
        else:
            if match_id > 1:
                # Search for the active series with a matching previous match that is closed
                for (team1, team2), info in active_series.items():
                    series_id = info['series_id']
                    
                    # Check if the previous match exists and its status is "Closed"
                    records = self.worksheet.get_all_records()
                    previous_match_closed = False

                    for row in records:
                        if (row['Series ID'] == series_id and
                            row['Match ID'] == previous_match_id and
                            row['Match Status'] == "Closed"):  # Ensure previous match is closed
                            previous_match_closed = True
                            break

                    # If the previous match exists and is closed, set up the current series
                    if previous_match_closed:
                        active_series[(team1, team2)]['current_match_id'] = match_id
                        series_info = active_series[(team1, team2)]
                        break

            if not series_info:
                await ctx.send("Previous match is not closed or does not exist. Please close the previous match or check the match ID.")
                print("No active series found for the given match ID, or previous match is not closed.")
                return
       
        # Extract team names and series ID from series_info
        team1 = series_info['team1']
        team2 = series_info['team2']
        series_id = series_info['series_id']

        full_team1 = self.teams.get(team1, team1)
        full_team2 = self.teams.get(team2, team2)

        print(f"Attempting to start Match ID {match_id} for Series ID {series_id}: Teams - {team1} vs {team2}")
        new_match_id = self.start_new_match(team1, team2, match_id)

        if not new_match_id:
            await ctx.send("There was an error starting the match. Please try again.")
            return

        await ctx.send(f"Started match {new_match_id} in series {series_id}: **{full_team1}** vs **{full_team2}**.")
        print("Match started message sent.")

        async def get_team_composition(ctx, team_name): # Helper function to get team compositions
            while True:
                await ctx.send(f"Please input the compositions for **{team_name}** (5 heroes, comma-separated):")
                print(f"Waiting for {team_name} input...")

                def check(msg):
                    return msg.channel == ctx.channel and msg.author == ctx.author  # Check if the message is from the command invoker

                try:
                    team_comp_msg = await self.bot.wait_for('message', check=check, timeout=90.0)
                    print(f"Received {team_name} composition: {team_comp_msg.content}")
                    if team_comp_msg.content.lower() == "cancel":
                        await ctx.send("Input canceled.")
                        return
                    
                    await ctx.send("One moment...")
                    # Process the hero input
                    matched_heroes, unmatched_heroes = self.hero_matcher.match_heroes(team_comp_msg.content)  # Process the input using HeroMatch

                    # Check if we have exactly 5 heroes
                    if len(matched_heroes) != 5:
                        await ctx.send("You must provide exactly 5 heroes for the composition! Please try again.")
                        print(f"{team_name} provided an invalid number of heroes.")
                        continue  # Prompt the user again

                    # Check for duplicates and validity
                    if "Invalid" in matched_heroes:
                        unmatched_heroes = [hero for hero in unmatched_heroes if hero.strip()]
                        await ctx.send(f"The following heroes did not match or are invalid: {', '.join(unmatched_heroes)}. Please try again.")
                        print(f"{team_name} provided unknown heroes: {', '.join(unmatched_heroes)}")
                        continue  # Prompt the user again

                    # Check for duplicates in the current series
                    duplicates = []
                    valid_heroes = []
                    for i, hero in enumerate(matched_heroes):
                        if not self.can_pick_hero(series_id, team_name, hero):
                            duplicates.append(hero)
                        else:
                            valid_heroes.append(hero)

                    if duplicates:
                        await ctx.send(f"The following heroes have already been picked by **{team_name}** in this series: {', '.join(duplicates)}! Please try again.")
                        print(f"{team_name} attempted to pick already chosen heroes: {', '.join(duplicates)}")
                        continue  # Prompt the user again
                    
                    for i, hero in enumerate(valid_heroes):
                        self.update_player_pick(series_id, new_match_id, team_name, i, hero)
                    # If everything is valid, send confirmation and return the team composition
                    await ctx.send(f"**{team_name}**'s composition has been recorded as:\n" + '\n'.join(f"• {hero}" for hero in matched_heroes) +"\nIs this correct? (Yes/No)")
                    try:
                        confirmation_msg = await self.bot.wait_for('message', check=check, timeout=30.0)
                        if confirmation_msg.content.capitalize() == "Yes":
                            return matched_heroes
                        elif confirmation_msg.content.capitalize() == "No":
                            self.clear_team_picks(series_id, new_match_id)
                            continue # Clear heroes and prompt the user again
                        else:
                            await ctx.send("Invalid response. Please respond with 'Yes' or 'No'.")
                    except asyncio.TimeoutError:
                        await ctx.send("You took too long to respond! Please try again.")
                        break

                except asyncio.TimeoutError:
                    await ctx.send(f"You took too long to respond! Please try again by using `!match {new_match_id}`.")
                    print(f"{team_name} did not respond in time, clearing hero inputs for match {new_match_id}")
                    self.clear_team_picks(series_id, new_match_id)
                    break

        # Get composition for Team 1
        team1_compositions = await get_team_composition(ctx, team1)
        if team1_compositions is None:
            return  # Exit if there was a timeout
        print("Team 1 comp added to sheets")
        # Get composition for Team 2
        team2_compositions = await get_team_composition(ctx, team2)
        if team2_compositions is None:
            return  # Exit if there was a timeout
        print("Team 2 comp added to sheets")

        # If both teams are valid, proceed to process them
        print(series_info)
        series_info['current_match_id'] += 1  
        print(f"Match ID incremented. Current Match ID is now {series_info['current_match_id']}.")
        await self.closematch(ctx, match_id)

    @commands.command()
    async def winner(self, ctx, match_id: int, winner: str):
        # Ensure the winner name is uppercase for consistency
        winner = winner.upper()

        # Print debug information
        print(f"Setting winner: '{winner}' for match ID {match_id}")
        full_name = self.teams.get(winner, winner)
        # Locate the series in active_series based on match_id
        series_id = None
        for (team1, team2), info in active_series.items():
            if info["current_match_id"] == match_id:
                series_id = info["series_id"]
                break

        # If series_id is not found, return an error
        if series_id is None:
            await ctx.send(f"No active series found with Match ID {match_id}.")
            return

        # Verify that the winner team name is valid
        if winner not in self.teams.keys():
            await ctx.send(f"Invalid team name '{winner}'. Please enter a valid team name.")
            return

        # Get all records to locate the correct match
        records = self.worksheet.get_all_records()
        print("Records from Google Sheets:", records)
        match_found = False

        # Loop through records to find the correct series and match
        for row_num, row in enumerate(records, start=2):  # Start from row 2 to account for header
            if row["Series ID"] == series_id and row["Match ID"] == match_id:
                match_found = True
                
                # Update the winner column in Google Sheets (Column 17)
                try:
                    self.worksheet.update_cell(row_num, 17, winner)  # Column 17 is the "Winner" column
                    
                    # Confirm the update in Discord
                    await ctx.send(f"Winner for match {match_id} in series {series_id} has been updated to **{full_name}**")
                    print(f"Winner for Match {match_id} in Series {series_id} updated to {winner}.")
                except Exception as e:
                    print("Error updating cell:", e)
                    await ctx.send("There was an error updating the winner. Please try again.")
                break

        if not match_found:
            await ctx.send(f"No match found with Series ID {series_id} and Match ID {match_id}.")

    @commands.command()
    async def closeseries(self, ctx, series_id: int):
        global active_series
        records = self.worksheet.get_all_records()  # Get all records from the worksheet
        match_found = False  # Track if the match was found

        for i, row in enumerate(records):
            # Check if this row corresponds to the match ID we want to close
            if row['Series ID'] == series_id and row['Series Status'] == 'Active':
                team1 = row['Team 1 Name']
                team2 = row['Team 2 Name']
                full_team1 = self.teams.get(team1, team1)
                full_team2 = self.teams.get(team2, team2)

                # Attempt to update the match status to closed
                try:
                    print(f"Updating Series ID {series_id} status to '{CLOSED_STATUS}' at row {i + 2}...")
                    self.worksheet.update_cell(i + 2, 5, CLOSED_STATUS)  # Assuming column 5 is for Series Status
                    self.worksheet.update_cell(i + 2, 6, CLOSED_STATUS)  # Assuming column 5 is for Match Status
                    print(f"Successfully updated Series ID {series_id} to status '{CLOSED_STATUS}'.")
                    
                    # Verification: Fetch the updated row to confirm the change
                    updated_row = self.worksheet.get_all_records()[i]
                    if updated_row['Series Status'] == CLOSED_STATUS:
                        match_found = True
                    else:
                        print(f"Warning: Series ID {series_id} status not updated correctly, found: {updated_row['Series Status']}")
                        
                except Exception as e:
                    print(f"Failed to update the match status for Match ID {series_id}: {e}")
                    await ctx.send("An error occurred while closing the match. Please try again.")
        active_series = {}
        await ctx.send(f"Closed series between **{full_team1}** and **{full_team2}**.")

        if not match_found:
            await ctx.send(f"No active series found with Series ID {series_id}.")

    @commands.command()
    async def closematch(self, ctx, match_id: int):
        records = self.worksheet.get_all_records()  # Get all records from the worksheet
        match_found = False  # Track if the match was found
        for i, row in enumerate(records):
            # Check if this row corresponds to the match ID we want to close
            if row['Match ID'] == match_id and row['Match Status'] == 'Active':
                team1 = row['Team 1 Name']
                team2 = row['Team 2 Name']
            # Attempt to update the match status to closed
                try:
                    print(f"Updating Match ID {match_id} status to '{CLOSED_STATUS}' at row {i + 2}...")
                    self.worksheet.update_cell(i + 2, 6, CLOSED_STATUS)  # Assuming column 6 is for Match Status
                    print(f"Successfully updated Match ID {match_id} to status '{CLOSED_STATUS}'.")
                    
                    # Verification: Fetch the updated row to confirm the change
                    updated_row = self.worksheet.get_all_records()[i]
                    if updated_row['Match Status'] == CLOSED_STATUS:
                        full_team1 = self.teams.get(team1, team1)
                        full_team2 = self.teams.get(team2, team2)
                        await ctx.send(f"The composition entry for match {match_id} between **{full_team1}** and **{full_team2}** has been successfully recorded.")
                        match_found = True
                    else:
                        print(f"Warning: Match ID {match_id} status not updated correctly, found: {updated_row['Match Status']}")
                        
                except Exception as e:
                    print(f"Failed to update the match status for Match ID {match_id}: {e}")
                    await ctx.send("An error occurred while closing the match. Please try again.")
                break  # Exit the loop once the match is found and updated

        if not match_found:
            await ctx.send(f"No active match found with ID {match_id}.")

    def close_match(self, match_id: int):
        records = self.worksheet.get_all_records()
        for i, row in enumerate(records):  # Enumerate to get the index
            # Check if the current match ID matches
            if row['Match ID'].strip() == match_id:  # Ensure match ID is checked as a string
                print(f"Found Match ID {match_id} at row {i + 2}: {row}")  # Debugging output
                if row['Match Status'].strip() == 'Active':  # Ensure match status is active
                    # Attempt to update the match status to closed
                    try:
                        print(f"Updating Match ID {match_id} status to '{CLOSED_STATUS}'...")
                        self.worksheet.update_cell(i + 2, 6, CLOSED_STATUS)  # Assuming column 6 is for Match Status
                        print(f"Successfully updated Match ID {match_id} to status '{CLOSED_STATUS}'.")
                        
                        # Verification: Fetch the updated row to confirm the change
                        updated_row = self.worksheet.get_all_records()[i]
                        if updated_row['Match Status'].strip() == CLOSED_STATUS:
                            print(f"Confirmed that Match ID {match_id} is now closed.")
                        else:
                            print(f"Warning: Match ID {match_id} status not updated correctly, found: {updated_row['Match Status']}")
                        
                    except Exception as e:
                        print(f"Failed to update the match status for Match ID {match_id}: {e}")
                    return
                else:
                    print(f"Match ID {match_id} is not active, cannot close.")
                    return

        print(f"No match found with Match ID: {match_id}.")  # For debugging

    def get_heroes_for_team_in_series(self, series_id, team_name):
        # Fetch all records from the Google Sheet
        records = self.worksheet.get_all_records()

        team_picks = {}

        # Loop through the records and find rows with the matching series ID
        for row in records:
            if row['Series ID'] == series_id:
                # Check if the row matches the team name (Team 1 or Team 2)
                match_id = row['Match ID']  # Assuming each row has a 'Match ID' field

                if row['Team 1 Name'] == team_name:
                    heroes = [
                        row['Team 1 Hero 1'], row['Team 1 Hero 2'], row['Team 1 Hero 3'],
                        row['Team 1 Hero 4'], row['Team 1 Hero 5']
                    ]
                elif row['Team 2 Name'] == team_name:
                    heroes = [
                        row['Team 2 Hero 1'], row['Team 2 Hero 2'], row['Team 2 Hero 3'],
                        row['Team 2 Hero 4'], row['Team 2 Hero 5']
                    ]
                else:
                    continue

                # Filter out empty hero names and store by match ID
                team_picks[match_id] = [hero for hero in heroes if hero]

        return team_picks

    @commands.command()
    async def seriespicks(self, ctx, series_id: int, team_name: str):
        """Display heroes picked by the team, organized by match within the series, in an embed."""
        
        full_name = self.teams.get(team_name.upper())
        picks_by_match = self.get_heroes_for_team_in_series(series_id, team_name.upper())

        if picks_by_match:
            embed = discord.Embed(
                title=f"{full_name}'s Heroes in series {series_id}",
                color=discord.Color.red()
            )

            # Add each match's picks as a field in the embed
            for match_id, heroes in sorted(picks_by_match.items()):
                formatted_heroes = "\n".join([f"- {hero.title()}" for hero in heroes])
                embed.add_field(
                    name=f"Match {match_id}",
                    value=formatted_heroes or "No heroes picked",
                    inline=True
                )

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"No picks found for **{full_name}** in series {series_id}.")

    async def pings(self, ctx, team1, team2, when: str = None):
        notification_channel_id = 1300568326606422086
        notification_channel = self.bot.get_channel(notification_channel_id)

        if notification_channel is None:
            print("Notification channel not found. Please check the configuration.")
            return

        # Get roles (your existing role fetching code)
        MVP = discord.utils.get(ctx.guild.roles, name="MVP on a Loss FeelsAbzeerMan")
        BCH = discord.utils.get(ctx.guild.roles, name="Barley's Chewies")
        TMT = discord.utils.get(ctx.guild.roles, name="Team Two")
        MRU = discord.utils.get(ctx.guild.roles, name='Memes "R" Us')
        CTZ = discord.utils.get(ctx.guild.roles, name="Confused Time Zoners")
        FLO = discord.utils.get(ctx.guild.roles, name="Floccinaucinihilipilification")
        PBR = discord.utils.get(ctx.guild.roles, name="Peanut Butter Randos")
        DOH = discord.utils.get(ctx.guild.roles, name="Disciples of the Highlord")

        if when == "next":
            if (team1 == "mvp" and team2 == "bch") or (
                team1 == "bch" and team2 == "mvp"):
                await self.notification_channel.send(f"{BCH.mention}, {MVP.mention}, you're up next!")
            elif (team1 == "ctz" and team2 == "tmt") or (
                team1 == "tmt" and team2 == "ctz"):
                await self.notification_channel.send(f"{CTZ.mention}, {TMT.mention}, you're up next!")
            elif (team1 == "doh" and team2 == "flo") or (
                team1 == "flo" and team2 == "doh"):
                await self.notification_channel.send(f"{DOH.mention}, {FLO.mention}, you're up next!")
            elif (team1 == "mru" and team2 == "pbr") or (
                team1 == "pbr" and team2 == "mru"):
                await self.notification_channel.send(f"{MRU.mention}, {PBR.mention}, you're up next!")
            else:
                print("Matchup not found.")
        elif when == "soon":
            if (team1 == "mvp" and team2 == "bch") or (
                team1 == "bch" and team2 == "mvp"):
                await self.notification_channel.send(f"{BCH.mention}, {MVP.mention}, keep an eye on this channel, your match might abe after this one.")
            elif (team1 == "ctz" and team2 == "tmt") or (
                team1 == "tmt" and team2 == "ctz"):
                await self.notification_channel.send(f"{CTZ.mention}, {TMT.mention}, keep an eye on this channel, your match might abe after this one.")
            elif (team1 == "doh" and team2 == "flo") or (
                team1 == "flo" and team2 == "doh"):
                await self.notification_channel.send(f"{DOH.mention}, {FLO.mention}, keep an eye on this channel, your match might abe after this one.")
            elif (team1 == "mru" and team2 == "pbr") or (
                team1 == "pbr" and team2 == "mru"):
                await self.notification_channel.send(f"{MRU.mention}, {PBR.mention}, keep an eye on this channel, your match might abe after this one.")
            else:
                print("Matchup not found.") 

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(CompTracker(bot))