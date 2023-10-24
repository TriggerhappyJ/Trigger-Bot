import yaml
import discord
import asyncio


# Get the max number of webhooks from the config file
with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)
    max_webhooks = config['max_webhooks']


async def manage_webhooks(channel, webhook, guild_id, config):
    # Find the guild's webhooks in the config
    guild_webhooks = next((entry for entry in config['guild_webhooks'] if entry['guild_id'] == guild_id), None)

    if guild_webhooks is None:
        guild_webhooks = {'guild_id': guild_id, 'webhooks': []}
        config['guild_webhooks'].append(guild_webhooks)

    if len(guild_webhooks['webhooks']) >= max_webhooks:
        # If the guild has reached its limit, remove the oldest entry
        delete_message = await channel.send("Reached max number of webhooks, deleting the oldest one <a:duckSpin:892990312732053544>")
        webhook_to_delete = guild_webhooks['webhooks'][0]

        oldest_webhook_channel = channel.guild.get_channel(webhook_to_delete['channel_id'])

        for webhook in await oldest_webhook_channel.webhooks():
            if webhook.id == webhook_to_delete['webhook_id']:
                print("Deleting webhook " + webhook.name + " from channel " + oldest_webhook_channel.name + " in guild " + oldest_webhook_channel.guild.name)
                await webhook.delete()
                await delete_message.delete()
                guild_webhooks['webhooks'].pop(0)
                break

    entry = {
        'channel_id': channel.id,
        'webhook_id': webhook.id,
        'webhook_url': webhook.url,
    }

    guild_webhooks['webhooks'].append(entry)

    with open('config.yml', 'w') as edit_config:
        yaml.dump(config, edit_config)


async def create_webhook_if_not_exists(channel, config, bot):
    webhooks = await channel.webhooks()
    existing_webhook = None
    for webhook in webhooks:
        if webhook.user == bot.user:
            existing_webhook = webhook
            break

    if existing_webhook is None:
        new_webhook = await channel.create_webhook(name=channel.name)
        await manage_webhooks(channel, new_webhook, channel.guild.id, config)
        webhook = new_webhook
        print("Created webhook for channel: " + channel.name + " in guild: " + channel.guild.name)
    else:
        webhook = existing_webhook
        print("Found an existing webhook for: " + channel.name + " in guild: " + channel.guild.name)

    return webhook


def clear_webhooks_for_guild(guild_id, config):
    # Find the guild's webhooks in the config
    guild_webhooks = next((entry for entry in config['guild_webhooks'] if entry['guild_id'] == guild_id), None)

    if guild_webhooks is not None:
        guild_webhooks['webhooks'] = []  # Clear the list of webhooks for this guild
        print(f"Cleared existing webhooks for guild with ID {guild_id}")

    with open('config.yml', 'w') as edit_config:
        yaml.dump(config, edit_config)
