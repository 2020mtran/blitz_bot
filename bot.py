import discord
import logging
import requests

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# Assume client refers to a discord.Client subclass...
client.run(token, log_handler=handler, log_level=logging.DEBUG)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

api_key = ""
api_url = ""

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
    


client.run('')