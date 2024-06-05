import discord
import logging
import requests

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# Assume client refers to a discord.Client subclass...
client.run(token, log_handler=handler, log_level=logging.DEBUG)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

api_key = "RGAPI-747a3755-9640-41c5-addd-be2e137ec919"
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
    


client.run('MTI0NzM1NTM1NTczNDg2ODAwOQ.GtGp3R.x7qhULV-q4UWM0bYj-s-YEMZVq0_u9MAYVoQCA')