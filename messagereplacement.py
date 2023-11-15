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
        else:
            button.style = discord.ButtonStyle.green
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Reddit", style=discord.ButtonStyle.green)
    async def reddit_button_callback(self, button, interaction):
        if button.style == discord.ButtonStyle.green:
            button.style = discord.ButtonStyle.red
        else:
            button.style = discord.ButtonStyle.green        
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="YT Shorts", style=discord.ButtonStyle.green)
    async def shorts_button_callback(self, button, interaction):
        if button.style == discord.ButtonStyle.green:
            button.style = discord.ButtonStyle.red
        else:
            button.style = discord.ButtonStyle.green        
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


async def update_replace_blacklist(ctx, add_to_list, config):
    user_id = ctx.author.id
    if add_to_list and user_id not in config['replace_blacklist']:
        config['replace_blacklist'].append(user_id)
        message = "Got it! I won't replace replace your links anymore <a:ralseiBoom:899406996007190549>"
        
        print("Added " + str(user_id) + " to replace_blacklist")
    elif not add_to_list and user_id in config['replace_blacklist']:
        config['replace_blacklist'].remove(user_id)
        message = "Got it! I'll start replacing your links again <a:ralseiBlunt:899401210870763610>"
        print("Removed " + str(user_id) + " from replace_blacklist")
    else:
        message = "You already have link replacements " + (
            "disabled" if add_to_list else "enabled") + " <a:duckSpin:892990312732053544>"

    with open('config.yml', 'w') as edit_config:
        yaml.dump(config, edit_config)

    sent_message = await ctx.send(message)
    view = replace_settings_view()
    await sent_message.edit(view=view)
