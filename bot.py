import discord
import logging
import requests
import asyncio

intents = discord.Intents.default()
intents.message_content = True

token = ""

client = discord.Client(intents=intents)

# handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# # Assume client refers to a discord.Client subclass...
# client.run(token, log_handler=handler, log_level=logging.DEBUG)

api_key = ""

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('$hello'):
        await message.channel.send('Hello!!')

    if message.content.startswith('$start'):
        await message.channel.send('Hello, to begin, what is your game name and tagline? (Ex: Doublelift #NA1)')

        account_api_url = "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"

        def is_valid(m):
            if m.author == message.author and "#" in m.content:
                print("Account is valid.")
                return True
            else:
                print("Account is invalid.")
                return False

        try: 
            userAccount = await client.wait_for('message', check=is_valid, timeout=30.0)
            await message.channel.send(f'Thank you! You entered: {userAccount.content}')
        except asyncio.TimeoutError:
            await message.channel.send("Response took too long. Please try again. (30s)")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

client.run(token)