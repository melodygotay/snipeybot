import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Tuple
import itertools
from itertools import combinations
from cogs.ranks import (Ranks, ranks)

class AccountManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sheet = self.auth_google_sheets()
        self.worksheet = self.sheet

    def auth_google_sheets(self):
        #Scope for sheets & drive
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        #Loading credentials from .json file
        creds = ServiceAccountCredentials.from_json_keyfile_name("C:\\Users\\LadyD\\AppData\\Local\\Programs\\Python\\Python312\\Projects\\HotsCalc\\snipey-bfcd3543a260.json", scope)
        #Authorizing a client to interact with sheets
        client = gspread.authorize(creds)
        #Open specific sheet
        sheet = client.open("Snipey data")
        #Access the first worksheet
        worksheet = sheet.get_worksheet(0)
        return worksheet
    
    def refresh_data(self):
        # Initialize the data variables
        self.discord_users = self.worksheet.col_values(1)  # Getting all users
        self.account_names = self.worksheet.col_values(2)  # Getting all account names
        self.ranks = self.worksheet.col_values(3)  # Getting all ranks

    def get_user_accounts(self):
        # Fetch all records from the sheet
        all_records = self.worksheet.get_all_records()
        return [(row['Account Name'], float(row['Rank'].split()[0])) for row in all_records]
    
    
    @commands.command(name="newacc")
    async def add_account(self, ctx: commands.Context, acc_name: str, rank: str, points: int):
        print(f"add_account command invoked by {ctx.author.name}")  # Debug line

        """
        Add a new account to the Google Sheet.
        Usage: !newacc <acc_name> <rank> <points>
        """
        self.refresh_data()
        try:
            rank_points = f"{rank} {points}"
            data = [ctx.author.name, acc_name, rank_points]
            self.account_names = self.sheet.col_values(2)  #Check for duplicates

            # Check if the account already exists
            if acc_name in self.account_names:
                await ctx.send(f"Account '{acc_name}' already exists! Try !update instead.")
                return

            # Append the data to the sheet
            self.worksheet.append_row(data)
            await ctx.send(f"Account '{acc_name}' added with rank {rank} {points}.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command(name="update")
    async def update_account(self, ctx: commands.Context, acc_name: str, rank: str, points: int):
        """
        Update an existing account's rank and points.
        Usage: !update <acc_name> <rank> <points>
        """
        self.refresh_data()
        try:
            # Combine rank and points into the required format
            rank_points = f"{rank} {points}"
            if acc_name not in self.account_names:
                await ctx.send(f"Account '{acc_name}' not found!")
                return

            # Find the row number of the account
            row_index = self.account_names.index(acc_name) + 1  # +1 for 1-based indexing

                # Check if the user is the account owner
            if self.worksheet.cell(row_index, 1).value != ctx.author.name:
                await ctx.send(f"You do not have permission to update the account '{acc_name}'.")
                return    
            
            self.worksheet.update_cell(row_index, 1, acc_name)  # Update the rank name
            # Update the rank column
            self.worksheet.update_cell(row_index, 3, rank_points)  # Update the rank with formatted string
            await ctx.send(f"Account '{acc_name}' updated with new rank '{rank}' and points '{points}'.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command(name="rmacc")
    async def delete_account(self, ctx: commands.Context, acc_name: str):
        """
        Delete an account from the Google Sheet.
        Usage: !rm <acc_name>
        """
        self.refresh_data()
        try:
            if acc_name not in self.account_names:
                await ctx.send(f"Account '{acc_name}' not found!")
                return

            # Find the row number of the account
            row_index = self.account_names.index(acc_name) + 1  # +1 for 1-based indexing

            # Check if the user is the account owner
            if self.worksheet.cell(row_index, 1).value != ctx.author.name:
                await ctx.send(f"You do not have permission to delete the account '{acc_name}'.")
                return
            
            # Delete the row
            self.worksheet.delete_rows(row_index)
            await ctx.send(f"Account '{acc_name}' has been deleted.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command(name="myaccs")
    async def retrieve_accounts(self, ctx: commands.Context, member: discord.Member = None):
        """
        Retrieve all accounts associated with the user.
        Usage: !myaccs
        """
        self.refresh_data()
        try:
            # If no member is mentioned, use the command issuer
            if member is None:
                discord_user = ctx.author.name
            else:
                discord_user = member.name
           
            # Fetch all records from the sheet
            all_records = self.worksheet.get_all_records()   

            # Find all accounts for the user
            user_accounts = [
                row for row in all_records if row['Discord User'] == discord_user
            ]

            if not user_accounts:
                await ctx.send(f"No accounts found for user '{discord_user}'.")
                return

            # Format the output
            account_list = "\n".join(
                f"{index + 1}. {row['Account Name']} Rank: {row['Rank'].upper()}" for index, row in enumerate(user_accounts)
            )
            final_message = f"**Accounts for {discord_user}:**\n```{account_list}```"
            await ctx.send(final_message)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")


    @commands.command(name="snipe")
    async def find_accounts(self, ctx: commands.Context, target_rank: str, points: int, num_accounts: int):
        """
        Find accounts that average as close as possible to the target rank.
        Usage: !snipe <RankLevel> <points> <num_accounts>
        Example: !snipe G1 500 2
        """
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

            # Fetch all the accounts from the Google Sheet
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

            # Send the result
            await ctx.send(f"Closest accounts to target rank **{target_rank.upper()} {points}**:\n{account_list_str}\n-------------------------\nThe average rank is **{avg_rank_name}{avg_rank_level} {avg_rank_points}**.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
              
# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(AccountManager(bot))