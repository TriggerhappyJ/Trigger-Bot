import yaml
import discord
import asyncio

with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)
    replacement_timeout = config['replacement_timeout']


async def handle_message_replacement(message, modified_message, worker, webhook, bot):
    author = message.author
    channel = message.channel
    reaction_emoji = "☠"

    print("Replacing message from: " + author.name + " in channel: " + channel.name)
    await message.delete()
    sent_message, webhook = await send_replacement_message(modified_message, author, channel, reaction_emoji, webhook)

    def check(message_reaction, user):
        return user == author and str(message_reaction.emoji) == reaction_emoji and message_reaction.message.id == sent_message.id

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=replacement_timeout, check=check)
        if reaction.emoji == reaction_emoji:
            await sent_message.delete()
    except asyncio.TimeoutError:
        await sent_message.clear_reaction(reaction_emoji)

    worker.cancel()


async def send_replacement_message(modified_message, author, channel, reaction_emoji, webhook):
    webhook_name = author.display_name
    avatar = author.guild_avatar.url if author.guild_avatar else author.avatar.url
    async with channel.typing():
        sent_message = await webhook.send(str(modified_message), username=webhook_name, avatar_url=avatar, wait=True)
        await sent_message.add_reaction(reaction_emoji)
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

    await ctx.respond(message)
