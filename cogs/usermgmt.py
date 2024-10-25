import discord
from discord.ext import commands, tasks
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import itertools
#from itertools import combinations
from cogs.ranks import ranks
from datetime import datetime
from dateutil import parser
from discord.utils import get

class AccountManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sheet = self.auth_google_sheets()
        self.worksheet = self.sheet

    def auth_google_sheets(self):
        #Scope for sheets & drive
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        #Load credentials from .json file
        creds = ServiceAccountCredentials.from_json_keyfile_name("", scope)
        client = gspread.authorize(creds) #Authorize client to interact with sheets
        sheet = client.open("Snipey data") # Open specific sheet
        worksheet = sheet.get_worksheet(0) # Access the first worksheet
        return worksheet
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.test_check_last_played() 

    @tasks.loop(hours=24)  # Adjust the interval as needed
    async def check_last_played(self):
        await self.bot.wait_until_ready()  # Ensure the bot is ready before running the task
        self.refresh_data()  # Refresh data from the sheet

        today = datetime.now()

        channel_id = 
        channel = self.bot.get_channel(channel_id)

        for index, row in enumerate(self.worksheet.get_all_records()):
            last_played_str = row['Last Played']
            discord_user = row['Discord User']
            acc_name = row['Account Name']
            if last_played_str and last_played_str.strip():
                try:
                    last_played_date = parser.parse(last_played_str)
                    days_since_last_played = (today - last_played_date).days  # Calculate the number of days since last played
                    member = get(channel.guild.members, name=discord_user)

                    if member:
                    # Create a mention string
                        if days_since_last_played == 14:  # Exactly 14 days
                            mention_string = f"Hey {member.mention}, it's been **14 days** since you last played on {acc_name}!"
                            await channel.send(mention_string)

                        elif days_since_last_played == 21:  # Exactly 21 days
                            mention_string = f"Hey {member.mention}, it's been **21 days** since you last played on {acc_name}!"
                            await channel.send(mention_string)

                        elif days_since_last_played > 21:
                            mention_string = f"Hey {member.mention}, it's been **{days_since_last_played} days** since you last played on {acc_name}!"
                            await channel.send(mention_string)
                
                except Exception as e:
                    print(f"Error parsing date for {discord_user}: {e}")

    @check_last_played.before_loop
    async def before_check_last_played(self):
        await self.bot.wait_until_ready()  # Wait until the bot is ready
        
    def refresh_data(self):  # Initialize the data variables
        self.discord_users = self.worksheet.col_values(1)  # Gets users
        self.account_names = self.worksheet.col_values(2)  # Gets account names
        self.ranks = self.worksheet.col_values(3)  # Gets ranks
        self.last_played = self.worksheet.col_values(4) # Gets last played data

    def get_user_accounts(self): # Get all records from the sheet
        all_records = self.worksheet.get_all_records()
        return [(row['Account Name'], float(row['Rank'].split()[0])) for row in all_records]
    
    @commands.command(name="newacc")
    async def add_account(self, ctx: commands.Context, acc_name: str, rank: str, points: int):
        print(f"add_account command invoked by {ctx.author.name}")  # Debug line
        # Adds a new account to the Google Sheet.
        # Usage: !newacc <acc_name> <rank> <points>
        self.refresh_data()
        account_name = acc_name.upper()
        try:
            # Prepare rank and points string
            rank_points = f"{rank} {points}"

            # Retrieve all records from the sheet to check for duplicates
            all_records = self.worksheet.get_all_records()

            # Check for duplicates: same user and account name
            for record in all_records:
                if record['Discord User'] == ctx.author.name and record['Account Name'] == account_name:
                    await ctx.send(f"{ctx.author.mention}, you already have an account named '{acc_name}' registered.")
                    return  # Exit the command to prevent adding the duplicate

            # If no duplicates found, add the new account
            data = [ctx.author.name, account_name, rank_points, "", acc_name]
            self.worksheet.append_row(data)  # Assuming this is how you add a row

            await ctx.send(f"{ctx.author.mention}, account '{acc_name}' added successfully with rank points: {rank_points}.")
        
        except Exception as e:
            await ctx.send(f"An error occurred while adding the account: {e}")

    @commands.command(name="update")
    async def update_account(self, ctx: commands.Context, acc_name: str, rank: str, points: int):
       # Update an existing account's rank and points.
       # Usage: !update <acc_name> <rank> <points>
        self.refresh_data()
        try:
            rank_points = f"{rank} {points}" # Combine rank and points into the required format
            if acc_name.upper() not in self.account_names:
                await ctx.send(f"Account '{acc_name.upper()}' not found!")
                return

            # Find the row number of the account
            row_index = self.account_names.index(acc_name.upper()) + 1  # +1 for 1-based indexing

            # Check if the user is the account owner
            if self.worksheet.cell(row_index, 1).value != ctx.author.name:
                await ctx.send(f"You do not have permission to update the account '{acc_name.upper()}'.")
                return    
            
            # Update the rank column
            self.worksheet.update_cell(row_index, 3, rank_points)  # Update the rank with formatted string
            await ctx.send(f"Account '{acc_name.upper()}' updated with new rank '{rank}' and points '{points}'.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command(name="rmacc")
    async def delete_account(self, ctx: commands.Context, acc_name: str):
        # Delete an account from the Google Sheet.
        # Usage: !rm <acc_name>
        self.refresh_data()
        try:
            if acc_name.upper() not in self.account_names:
                await ctx.send(f"Account '{acc_name.upper()}' not found!")
                return

            # Find the row number of the account
            row_index = self.account_names.index(acc_name.upper()) + 1

            # Check if the user is the account owner
            if self.worksheet.cell(row_index, 1).value != ctx.author.name:
                await ctx.send(f"You do not have permission to delete the account '{acc_name.upper()}'.")
                return
            
            self.worksheet.delete_rows(row_index)  # Delete the row
            await ctx.send(f"Account '{acc_name.upper()}' has been deleted.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command(name="myaccs")
    async def retrieve_accounts(self, ctx: commands.Context, member: discord.Member = None):
        # Retrieve all accounts associated with the user.
        # Usage: !myaccs
        self.refresh_data()
        try:  
            if member is None: # If no member is mentioned, use the command issuer
                discord_user = ctx.author.name
            else:
                discord_user = member.name
        
            all_records = self.worksheet.get_all_records()   

            # Find all accounts for the user
            user_accounts = [
                row for row in all_records if row['Discord User'] == discord_user
            ]
            if not user_accounts:
                await ctx.send(f"No accounts found for user '{discord_user}'.")
                return

            rank_length = max(len(row['Rank']) for row in user_accounts)

            embed = discord.Embed(
                title = f"**Accounts for {discord_user}:**",
                color=discord.Color.purple()
            )
            # Format the output
            for index, row in enumerate(user_accounts):
                # Account info string with rank and last played
                account_info = f"Rank: `{row['Rank'].upper().ljust(rank_length)}`"
                if row['Last Played']:
                    account_info += f" |   Last played: `{row['Last Played']}`\n"

                # Add account information as a field in the embed
                embed.add_field(
                    name=f"{index + 1}. {row['Display']}",
                    value=account_info,
                    inline=False
                )

            embed.set_footer(text=f"- - - Requested by {ctx.author.display_name} - - -")

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
            
    @commands.command(name="snipe")
    async def find_accounts(self, ctx: commands.Context, target_rank: str, points: int, num_accounts: int, *usernames: str):
        # Find accounts that average as close as possible to the target rank.
        # Usage: !snipe <RankLevel> <points> <num_accounts> [usernames...]
        # Example: !snipe G1 500 2 @user1 @user2
        try:
            # Validate target rank format
            if len(target_rank) < 2 or not target_rank[:-1].isalpha() or not target_rank[-1].isdigit():
                await ctx.send("Invalid target rank format. Please use 'RankLevel Points'. Example: G1 500")
                return
            
            rank_name = target_rank[:-1].upper()
            level = target_rank[-1]

            if rank_name not in ranks or level not in ranks[rank_name]:
                await ctx.send(f"Invalid target rank '{target_rank}'.")
                return

            # Convert target rank to points
            target_base_points = ranks[rank_name][level][0]
            target_total_points = target_base_points + points

            all_records = self.worksheet.get_all_records()

            # Prepare a dictionary to group accounts by user
            accounts_by_user = {}
            for record in all_records:
                rank_and_level = record['Rank']
                discord_user = record['Discord User']
                account_name = record['Account Name']

                parts = rank_and_level.split()
                if len(parts) != 2:
                    continue

                rank_name = parts[0][:-1].upper()
                level = parts[0][-1]
                points_str = parts[1]
                if rank_name in ranks and level in ranks[rank_name]:
                    base_points = ranks[rank_name][level][0]
                    total_points = base_points + int(points_str)

                    if discord_user not in accounts_by_user:
                        accounts_by_user[discord_user] = []
                    accounts_by_user[discord_user].append((account_name, total_points))

            # Create a list of unique users
            unique_users = list(accounts_by_user.keys())

            # Handle mentions
            if ctx.message.mentions:
                mentioned_users = [user.name for user in ctx.message.mentions]
                unique_users = [user for user in unique_users if user in mentioned_users]

            closest_combination = None
            closest_average = float('inf')  # Set to infinity for comparison

            # Generate combinations of users
            for user_combination in itertools.combinations(unique_users, num_accounts):
                # Create all possible combinations of accounts for these users
                user_accounts = [accounts_by_user[user] for user in user_combination]

                # Get all combinations of accounts for the selected users
                accounts = list(itertools.product(*user_accounts))

                # Check each combination of accounts
                for account_combination in accounts:
                    average_points = sum(account[1] for account in account_combination) / len(account_combination)

                    # Calculate the difference to the target total points
                    diff = abs(average_points - target_total_points)

                    # Check if this combination is closer to the target
                    if diff < closest_average:
                        closest_average = diff
                        closest_combination = account_combination
                        closest_user_combination = user_combination  # Save the corresponding users

            # If no combination was found
            if closest_combination is None:
                await ctx.send("Not enough unique users found with suitable accounts.")
                return

            # Prepare the output with correct pairing
            account_list = []
            for user, account in zip(closest_user_combination, closest_combination):
                account_name, total_points = account
                account_list.append(f"**-{account_name}** - {user}")

            # Join the account list for display
            account_list_str = "\n".join(account_list)

            # Prepare average rank calculation
            avg_points = sum(account[1] for account in closest_combination) / len(closest_combination)
            avg_rank_name, avg_rank_level, avg_rank_points = None, None, None

            # Convert average points back into rank
            for rank_name, levels in ranks.items():
                for level, (lower, upper) in levels.items():
                    if lower <= avg_points <= upper:
                        avg_rank_name = rank_name
                        avg_rank_level = level
                        avg_rank_points = int(round(avg_points - lower))
                        break

            await ctx.send(f"Closest accounts to target rank **{target_rank.upper()} {points}**:\n{account_list_str}\n-------------------------\nThe average rank is **{avg_rank_name}{avg_rank_level} {avg_rank_points}**.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")


    def parse_date(self, month: str = None, day: int = None, year: int = None):
        today = datetime.today()

        # Assign defaults if month, day, or year are not provided
        month = int(month) if month else today.month
        day = int(day) if day else today.day
        year = int(year) if year else today.year

        return datetime(year, month, day).date()

    @commands.command(name="played")
    async def played(self, ctx: commands.Context, acc_name: str, month: str = None, day: int = None, year: int = None):
        self.refresh_data()
        account_name = acc_name.upper()

        # Default to today's date if month, day, or year are not provided
        if month is None and day is None and year is None:
            last_played_date = datetime.today().date()
        else:
            try:
                last_played_date = self.parse_date(month, day, year)  # Custom parsing method
            except Exception as e:
                await ctx.send(f"Error parsing date: {e}")
                return

        # Convert the date object to a string
        last_played_date_str = last_played_date.strftime("%Y-%m-%d")

        # Debugging output to check if date was parsed correctly
        print(f"Updating account {account_name} with last played date: {last_played_date_str}")

        if account_name in self.account_names:
            account_row = self.account_names.index(account_name) + 1
            print(f"Found account {account_name} at row {account_row}")

            # Update the worksheet with the parsed date
            try:
                self.worksheet.update_cell(account_row, 4, last_played_date_str)
                await ctx.send(f"{ctx.author.mention}, the 'Last Played' date for '{acc_name}' has been updated to {last_played_date_str}.")
            except Exception as e:
                await ctx.send(f"Failed to update the worksheet: {e}")
                print(f"Error updating cell at row {account_row}, column 4: {e}")
        else:
            # If the account name is not found
            await ctx.send(f"{ctx.author.mention}, the account '{acc_name}' was not found in the database.")
            print(f"Account {account_name} not found in account_names.")

    @commands.command(name="lastplayed")
    async def last_played(self, ctx, *, account_name: str):
        discord_user = ctx.author.name  # Get the Discord username

        # Fetch all records from the Google Sheet
        all_records = self.worksheet.get_all_records()

        # Find the row corresponding to the user and the specified account name
        user_record = next((row for row in all_records if row['Discord User'] == discord_user and row['Account Name'] == account_name), None)

        if user_record is None:
            await ctx.send(f"No record found for user '{discord_user}' with account '{account_name}'.")
            return

        last_played_str = user_record['Last Played']
        
        if not last_played_str or not last_played_str.strip():
            await ctx.send(f"{discord_user}, no last played date is set for the account '{account_name}'.")
            return

        try:
            last_played_date = parser.parse(last_played_str)
            days_since_last_played = (datetime.now() - last_played_date).days

            await ctx.send(f"{ctx.author.mention}, it has been **{days_since_last_played} days** since you last played on the account '{account_name}'.")
        except Exception as e:
            await ctx.send(f"Error parsing last played date for {discord_user}: {e}")

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(AccountManager(bot))