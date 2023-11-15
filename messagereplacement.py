import yaml
import discord
import asyncio

with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)
    replacement_timeout = config['replacement_timeout']

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
            config['replace_blacklist'][interaction.user.id].append('https://twitter.com/')
            config['replace_blacklist'][interaction.user.id].append('https://x.com/')
        else:
            button.style = discord.ButtonStyle.green
            config['replace_blacklist'][interaction.user.id].remove('https://twitter.com/')
            config['replace_blacklist'][interaction.user.id].remove('https://x.com/')
        with open('config.yml', 'w') as config_file:
            yaml.dump(config, config_file)
        await interaction.response.edit_message(view=self)
    
    @discord.ui.button(label="Reddit", style=discord.ButtonStyle.green)
    async def reddit_button_callback(self, button, interaction):
        if button.style == discord.ButtonStyle.green:
            button.style = discord.ButtonStyle.red
            config['replace_blacklist'][interaction.user.id].append('https://www.reddit.com/')
            config['replace_blacklist'][interaction.user.id].append('https://old.reddit.com/')
        else:
            button.style = discord.ButtonStyle.green
            config['replace_blacklist'][interaction.user.id].remove('https://www.reddit.com/')
            config['replace_blacklist'][interaction.user.id].remove('https://old.reddit.com/')
        with open('config.yml', 'w') as config_file:
            yaml.dump(config, config_file)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="YT Shorts", style=discord.ButtonStyle.green)
    async def shorts_button_callback(self, button, interaction):
        if button.style == discord.ButtonStyle.green:
            button.style = discord.ButtonStyle.red
            config['replace_blacklist'][interaction.user.id].append('https://www.youtube.com/shorts/')
        else:
            button.style = discord.ButtonStyle.green
            config['replace_blacklist'][interaction.user.id].remove('https://www.youtube.com/shorts/')
        with open('config.yml', 'w') as config_file:
            yaml.dump(config, config_file)
        await interaction.response.edit_message(view=self)


async def handle_message_replacement(message, modified_message, worker, webhook, bot):
    author = message.author
    channel = message.channel

    print("Replacing message from: " + author.name + " in channel: " + channel.name)
    await message.delete()
    sent_message, webhook = await send_replacement_message(modified_message, author, channel, webhook)

    view = message_delete_view()
    await sent_message.edit(view=view)

    await asyncio.sleep(replacement_timeout)
    await sent_message.edit(view=None)

    worker.cancel()


async def send_replacement_message(modified_message, author, channel, webhook):
    webhook_name = author.display_name
    avatar = author.guild_avatar.url if author.guild_avatar else author.avatar.url
    async with channel.typing():
        sent_message = await webhook.send(str(modified_message), username=webhook_name, avatar_url=avatar, wait=True)
    return sent_message, webhook


async def replace_blacklist_settings(ctx, worker):
    config.get('replace_blacklist', set())

    # If the user is not in the replace_blacklist dict, add them
    if ctx.author.id not in config['replace_blacklist']:
        config['replace_blacklist'][ctx.author.id] = []
        with open('config.yml', 'w') as config_file:
            yaml.dump(config, config_file)

    user_id = ctx.author.id
    # Send embed message
    embed = discord.Embed(title="Link Replacement Settings", description="Select which types of links you would like to be replaced.", color=0xc01e2e)
    view = replace_settings_view()

    # Set all of the buttons in the view to the correct state
    if user_id in config['replace_blacklist']:
        if "https://twitter.com/" in config['replace_blacklist'][user_id]:
            view.children[0].style = discord.ButtonStyle.red
        if "https://www.reddit.com/" in config['replace_blacklist'][user_id]:
            view.children[1].style = discord.ButtonStyle.red
        if "https://www.youtube.com/shorts/" in config['replace_blacklist'][user_id]:
            view.children[2].style = discord.ButtonStyle.red

    message = await ctx.respond(embed=embed, view=view, ephemeral=True)
    await asyncio.sleep(60)
    worker.cancel()
