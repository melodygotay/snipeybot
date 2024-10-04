import discord
from discord.ext import commands
from collections import defaultdict
import asyncio

# Ranks dictionary
ranks = {
    "B": {
        "5": (0, 999),
        "4": (1000, 1999),
        "3": (2000, 2999),
        "2": (3000, 3999),
        "1": (4000, 4999),
    },
    "S": {
        "5": (5000, 5999),
        "4": (6000, 6999),
        "3": (7000, 7999),
        "2": (8000, 8999),
        "1": (9000, 9999),
    },
    "G": {
        "5": (10000, 10999),
        "4": (11000, 11999),
        "3": (12000, 12999),
        "2": (13000, 13999),
        "1": (14000, 14999),
    },
    "P": {
        "5": (15000, 15999),
        "4": (16000, 16999),
        "3": (17000, 17999),
        "2": (18000, 18999),
        "1": (19000, 19999),
    },
    "D": {
        "5": (20000, 20999),
        "4": (21000, 21999),
        "3": (22000, 22999),
        "2": (23000, 23999),
        "1": (24000, 24999),
    },
}

input_ranks = defaultdict(list)  # Maps user_id to a list of rank points
original_inputs = defaultdict(list)  # Maps user_id to a list of the original rank inputs

class Ranks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def confirmation_delete(self, confirmation: discord.Message, time: int):
        await asyncio.sleep(time)  # Time in seconds   
        try:
            await confirmation.delete()
        except discord.HTTPException:
            pass  # Ignore if the message is not found

    @commands.command()
    async def rank(self, ctx, *args):
        user_id = ctx.author.id  # Get the unique ID of the user

        # Clear previous input ranks for the user
        input_ranks[user_id].clear()
        original_inputs[user_id].clear()

        # Ensure there is an even number of arguments (pairs of rank-level and points)
        if len(args) % 2 != 0:
            await ctx.send("Please provide pairs of rank-level and points.")
            return
        
        for i in range(0, len(args), 2):
            user_input = f"{args[i]} {args[i + 1]}".strip()  # Combine the rank-level and points for processing

            # Store the original input for later use
            original_inputs[user_id].append(user_input)  # Store the exact input

            try:
                # Split the input into rank-level and points
                parts = user_input.split()

                # Validate input format
                if len(parts) < 2:
                    await ctx.send(f"Invalid input format: {user_input.strip()}. Please use 'RankLevel Points' format.")
                    return

                rank_and_level = parts[0]  # Example: G1 or S2
                points_str = parts[1]  # Points part, e.g., "500"

                # Validate rank and level format (Rank must be letters, level must be a digit)
                if len(rank_and_level) < 2 or not rank_and_level[:-1].isalpha() or not rank_and_level[-1].isdigit():
                    await ctx.send(f"Invalid rank format: {rank_and_level.strip()}. Please use 'RankLevel Points' format.")
                    return

                rank_name = rank_and_level[:-1].upper()  # Rank (G, S, etc.)
                level = rank_and_level[-1]  # Level (1, 2, etc.)
                points = int(points_str)  # Points to integer

                # Check if rank and level are valid
                if rank_name in ranks and level in ranks[rank_name]:
                    base_points = ranks[rank_name][level][0]  # Get base points for that rank
                    total_points = base_points + points  # Add input points to base points
                    input_ranks[user_id].append(total_points)  # Append to user's input_ranks
                else:
                    await ctx.send(f"Invalid rank or level: {rank_name}{level}.")
                    return

            except (ValueError, IndexError):
                await ctx.send(f"Invalid input format: {user_input.strip()}. Please use 'RankLevel Points' format.")

        # If all inputs are valid, acknowledge the input
        confirmation = await ctx.send(f"{ctx.author.mention}, ranks and points have been added!")
        await self.confirmation_delete(confirmation, 10)

    @commands.command()
    async def ranklist(self, ctx):
        user_id = ctx.author.id  # Get the unique ID of the user
        user_inputs = original_inputs[user_id]  # Retrieve the user's original inputs

        if not user_inputs:
            await ctx.send("No ranks have been entered yet.")
        else:
            # Format the ranks into a numbered list
            ranks_list = "\n".join(f"{index + 1}. {rank}" for index, rank in enumerate(user_inputs))
            await ctx.send(f"**Entered ranks:**\n{ranks_list}")

    @commands.command()
    async def delete(self, ctx, index: int):
        user_id = ctx.author.id  # Get the unique ID of the user
        user_inputs = original_inputs[user_id]  # Retrieve the user's original inputs

        if index < 1 or index > len(user_inputs):
            await ctx.send("Invalid index. Please provide a valid rank number.")
            return

        removed_rank = user_inputs.pop(index - 1)  # Remove the rank at the specified index
        input_ranks[user_id].pop(index - 1)  # Remove the corresponding points from input_ranks
        confirmation = await ctx.send(f"Rank '{removed_rank}' has been deleted!")
        await self.confirmation_delete(confirmation, 10)

    # Command to clear ranks
    @commands.command()
    async def reset(self, ctx):
        user_id = ctx.author.id  # Get the unique ID of the user
        input_ranks[user_id].clear()  # Clear the user's specific ranks
        original_inputs[user_id].clear()  # Clear the user's specific original inputs
        command_message = ctx.message
        confirmation = await ctx.send("All your ranks have been cleared.")
        await self.confirmation_delete(command_message, 5)
        await self.confirmation_delete(confirmation, 10)
   
    # Example: average rank calculation command
    @commands.command()
    async def avg(self, ctx):
        user_id = ctx.author.id  # Get the unique ID of the user
        user_points = input_ranks[user_id]  # Retrieve the user's points

        if not user_points:  # Check if the list is empty
            await ctx.send("You haven't entered any ranks yet!")
            return

        avg_rank = self.calculate_avg(user_points)
        await ctx.send(avg_rank)

    def calculate_avg(self, points_list):
        total_points = sum(points_list)
        players = len(points_list)

        if players == 0:
            return "No ranks provided."

        average = total_points / players

        for rank_name, levels in ranks.items():
            for level, (lower, upper) in levels.items():
                if lower <= average <= upper:
                    diff = int(round(average - lower))
                    return f"Average rank: {rank_name}{level} {diff} points."
        
        return "Rank not found."

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(Ranks(bot))