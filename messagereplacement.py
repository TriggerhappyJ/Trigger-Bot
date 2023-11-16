import yaml
import discord
import asyncio

with open('yaml/replaceblacklist.yml', 'r') as blacklist_file:
    replace_blacklist = yaml.safe_load(blacklist_file)

class message_delete_view(discord.ui.View):
    @discord.ui.button(label="", style=discord.ButtonStyle.red, emoji="🗑")
    async def button_callback(self, button, interaction):
        await interaction.response.send_message("Message has been deleted!", ephemeral=True)
        if interaction.message:
            await interaction.message.delete()


class replace_settings_view(discord.ui.View):
    @discord.ui.button(label="Twitter", style=discord.ButtonStyle.green)
    async def twitter_button_callback(self, button, interaction):
        if button.style == discord.ButtonStyle.green:
            button.style = discord.ButtonStyle.red
            replace_blacklist['user_replace_blacklist'][interaction.user.id].append('https://twitter.com/')
            replace_blacklist['user_replace_blacklist'][interaction.user.id].append('https://x.com/')
        else:
            button.style = discord.ButtonStyle.green
            replace_blacklist['user_replace_blacklist'][interaction.user.id].remove('https://twitter.com/')
            replace_blacklist['user_replace_blacklist'][interaction.user.id].remove('https://x.com/')
        with open('yaml/replaceblacklist.yml', 'w') as blacklist_file:
            yaml.dump(replace_blacklist, blacklist_file)
        await interaction.response.edit_message(view=self)
    
    @discord.ui.button(label="Reddit", style=discord.ButtonStyle.green)
    async def reddit_button_callback(self, button, interaction):
        if button.style == discord.ButtonStyle.green:
            button.style = discord.ButtonStyle.red
            replace_blacklist['user_replace_blacklist'][interaction.user.id].append('https://www.reddit.com/')
            replace_blacklist['user_replace_blacklist'][interaction.user.id].append('https://old.reddit.com/')
        else:
            button.style = discord.ButtonStyle.green
            replace_blacklist['user_replace_blacklist'][interaction.user.id].remove('https://www.reddit.com/')
            replace_blacklist['user_replace_blacklist'][interaction.user.id].remove('https://old.reddit.com/')
        with open('yaml/replaceblacklist.yml', 'w') as blacklist_file:
            yaml.dump(replace_blacklist, blacklist_file)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="YT Shorts", style=discord.ButtonStyle.green)
    async def shorts_button_callback(self, button, interaction):
        if button.style == discord.ButtonStyle.green:
            button.style = discord.ButtonStyle.red
            replace_blacklist['user_replace_blacklist'][interaction.user.id].append('https://www.youtube.com/shorts/')
        else:
            button.style = discord.ButtonStyle.green
            replace_blacklist['user_replace_blacklist'][interaction.user.id].remove('https://www.youtube.com/shorts/')
        with open('yaml/replaceblacklist.yml', 'w') as blacklist_file:
            yaml.dump(replace_blacklist, blacklist_file)
        await interaction.response.edit_message(view=self)


async def handle_message_replacement(message, modified_message, worker, webhook, bot):
    author = message.author
    channel = message.channel

    print("Replacing message from: " + author.name + " in channel: " + channel.name)
    await message.delete()
    sent_message, webhook = await send_replacement_message(modified_message, author, channel, webhook)

    view = message_delete_view()
    await sent_message.edit(view=view)

    await asyncio.sleep(30)
    await sent_message.edit(view=None)
    worker.cancel()


async def send_replacement_message(modified_message, author, channel, webhook):
    webhook_name = author.display_name
    avatar = author.guild_avatar.url if author.guild_avatar else author.avatar.url
    async with channel.typing():
        sent_message = await webhook.send(str(modified_message), username=webhook_name, avatar_url=avatar, wait=True)
    return sent_message, webhook


async def replace_blacklist_settings(ctx, worker):
    replace_blacklist.get('user_replace_blacklist', set())
    # If the user is not in the replace_blacklist dict, add them
    if ctx.author.id not in replace_blacklist['user_replace_blacklist']:
        replace_blacklist['user_replace_blacklist'][ctx.author.id] = []
        with open('yaml/replaceblacklist.yml', 'w') as blacklist_file:
            yaml.dump(replace_blacklist, blacklist_file)

    user_id = ctx.author.id
    # Send embed message
    embed = discord.Embed(title="Link Replacement Settings", description="Select which types of links you would like to be replaced.", color=0xc01e2e)
    embed.set_footer(text="This popup will close in 60 seconds.")
    view = replace_settings_view()

    # Set all of the buttons in the view to the correct state
    if user_id in replace_blacklist['user_replace_blacklist']:
        if "https://twitter.com/" in replace_blacklist['user_replace_blacklist'][user_id]:
            view.children[0].style = discord.ButtonStyle.red
        if "https://www.reddit.com/" in replace_blacklist['user_replace_blacklist'][user_id]:
            view.children[1].style = discord.ButtonStyle.red
        if "https://www.youtube.com/shorts/" in replace_blacklist['user_replace_blacklist'][user_id]:
            view.children[2].style = discord.ButtonStyle.red

    message = await ctx.respond(embed=embed, view=view, ephemeral=True)
    # Count down the 60 seconds on the message in 5 second intervals
    for i in range(12):
        await asyncio.sleep(5)
        embed.set_footer(text=f"This popup will close in {60 - (i + 1) * 5} seconds.")
        await message.edit_original_response(embed=embed, view=view)

    await message.delete_original_response()
    worker.cancel()
