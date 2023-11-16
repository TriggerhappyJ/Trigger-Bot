import yaml
import discord
import asyncio

# Get the max number of webhooks from the config file
with open('yaml/config.yml', 'r') as config_file:
    webhook_config = yaml.safe_load(config_file)
    max_webhooks = webhook_config['max_webhooks']


async def manage_webhooks(channel, webhook, guild_id, config, guild_name):
    # Find the guild's webhooks in the config
    guilds = next((entry for entry in config['guilds'] if entry['guild_id'] == guild_id), None)

    #if guilds is None:
    #    guilds = {'guild_id': guild_id, 'guild_name': guild_name, 'webhooks': [], 'current_games_channels': [], 'upcoming_games_channels': []}
     #   config['guilds'].append(guilds)

    if len(guilds['webhooks']) >= max_webhooks:
        # If the guild has reached its limit, remove the oldest entry
        delete_message = await channel.send(
            "Reached max number of webhooks, deleting the oldest one <a:duckSpin:892990312732053544>")
        webhook_to_delete = guilds['webhooks'][0]

        oldest_webhook_channel = channel.guild.get_channel(webhook_to_delete['channel_id'])

        for webhook in await oldest_webhook_channel.webhooks():
            if webhook.id == webhook_to_delete['webhook_id']:
                print(
                    "Deleting webhook " + webhook.name + " from channel " + oldest_webhook_channel.name + " in guild " + oldest_webhook_channel.guild.name)
                await webhook.delete()
                await delete_message.delete()
                guilds['webhooks'].pop(0)
                break

    entry = {
        'channel_id': channel.id,
        'webhook_id': webhook.id,
        'webhook_url': webhook.url,
    }

    guilds['webhooks'].append(entry)

    with open('yaml/config.yml', 'w') as edit_config:
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
        await manage_webhooks(channel, new_webhook, channel.guild.id, config, channel.guild.name)
        webhook = new_webhook
        print("Created webhook for channel: " + channel.name + " in guild: " + channel.guild.name)
    else:
        webhook = existing_webhook
        print("Found an existing webhook for: " + channel.name + " in guild: " + channel.guild.name)

    return webhook


def clear_webhooks_for_guild(guild_id, config):
    # Find the guild's webhooks in the config
    guilds = next((entry for entry in config['guilds'] if entry['guild_id'] == guild_id), None)

    if guilds is not None:
        guilds['webhooks'] = []  # Clear the list of webhooks for this guild
        print(f"Cleared existing webhooks for guild with ID {guild_id}")

    with open('yaml/config.yml', 'w') as edit_config:
        yaml.dump(config, edit_config)


async def handle_webhook_startup(bot, config):
    for guild in bot.guilds:
        # Find if the guild is in config, if not then add an entry for it
        guilds = next((entry for entry in config['guilds'] if entry['guild_id'] == guild.id), None)
        if guilds is None:
            guilds = {'guild_id': guild.id, 'guild_name': guild.name, 'webhooks': [], 'current_games_channels': [], 'upcoming_games_channels': [], 'replacement_timeout': 30}
            config['guilds'].append(guilds)
            with open('yaml/config.yml', 'w') as edit_config:
                yaml.dump(config, edit_config)

        for channel in guild.text_channels:
            webhooks = await channel.webhooks()
            for webhook in webhooks:
                # If the bot has created the webhook, save it in the config file
                if webhook.user == bot.user:
                    print("Saving webhook " + webhook.name + " in guild " + webhook.guild.name)
                    await manage_webhooks(channel, webhook, guild.id, config, webhook.guild.name)
