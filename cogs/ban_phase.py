import discord
from discord.ext import commands
import random
from data.game_data import MAPS
import asyncio

class BanPhase(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.maps = MAPS

    @commands.command()
    async def maps(self, ctx: commands.Context):
        embed = discord.Embed(
            title="3k Raviment Map Pool",
            color=discord.Color.red()
        )
        embed.add_field(name="", value='\n'.join(['- ' + map_name for map_name in self.maps]), inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def flip(self, ctx: commands.Context):
        result = random.choice(["map ban", "first pick"])
        await ctx.send(f"{ctx.author.mention}, your team gets: {result}")

    @commands.command()
    async def ban(self, ctx: commands.Context, user: discord.Member):
        remaining_maps = self.maps.copy()  # Create a copy of the maps list
        rounds = 2
        users = [ctx.author, user]  # User 1 and User 2
        current_user_index = 0  # Start with User 1

        for round_number in range(1, rounds + 1):
            for _ in range(2):  # Each user gets two turns per round
                current_user = users[current_user_index]

                while True:  # Loop until the user provides valid input
                    await ctx.send(f"{current_user.mention}, please name a map to remove:\nRemaining maps: {', '.join(remaining_maps)}")

                    def check(msg):
                        return msg.author == current_user and msg.channel == ctx.channel

                    try:
                        user_input = await self.bot.wait_for('message', check=check, timeout=45.0)  # 45 seconds to respond
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
            #await ctx.send(f"Remaining maps after ban phase:\n{'\n- '.join(remaining_maps)}")
        else:
            await ctx.send("No maps remain.")





# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(BanPhase(bot))