import discord
import logging
import requests
import asyncio
import pymongo
from config import DISCORD_TOKEN, MONGO_CONNECTION_STRING, RIOT_API_KEY

# Discord Client Initialization
intents = discord.Intents.default()
intents.message_content = True

token = DISCORD_TOKEN
client = discord.Client(intents=intents)

# MongoDB Connection
connection_string = MONGO_CONNECTION_STRING
m_client = pymongo.MongoClient(connection_string)

# Access database
db = m_client["Cluster0"]

api_key = RIOT_API_KEY

user_data = {}

class ConfirmView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=30) # From the discord.ui.view super class
        self.value = None # Result of button (later)
        self.author = author # User who initated the interaction

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("This button is not for you.", ephemeral=True)
            return
        self.value = True
        await interaction.response.edit_message(content="Confirmed!", view=None)  # Update the message to show it's confirmed
        self.stop()

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("This button is not for you.", ephemeral=True)
            return
        self.value = False
        await interaction.response.edit_message(content="Confirmed!", view=None)  # Update the message to show it's confirmed
        self.stop()

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
        user_id = message.author.id
        user_info = db["user-data"]
        user_record = user_info.find_one({"_id": str(user_id)})

        print(user_record)
        if user_record:
            info = user_record
            confirm_view_replace = ConfirmView(message.author)
            await message.channel.send(f"You already have an account linked: {info['account_name']}{info['tag_line']}. Would you like to link a different account? (Warning: This will override your current data.)", view=confirm_view_replace)
            await confirm_view_replace.wait()

            if confirm_view_replace.value is None:
                await message.channel.send("Confirmation timed out. Please try again.")
                return
            elif confirm_view_replace.value:
                user_info.delete_one({"_id": str(user_id)})
                del user_data [user_id]
                await message.channel.send("Your account is now delinked. You can now use the $start command again to link a new Riot account.")
            else:
                await message.channel.send("Your data has not been reset.")
                return

        await message.channel.send('Hello, to begin, what is your game name? Do not enter your Riot tag yet. (Ex: Doublelift)')

        account_api_url = "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"

        def nameIsValid(m):
            if m.author == message.author and "#" not in m.content:
                print("Account name is in the right format.")
                return True
            else:
                print("Account is not in the right format.")
                return False
        
        def tagIsValid(m):
            if m.author == message.author and "#" in m.content:
                print("Account tag is in the correct format.")
                return True
            else:
                print("Account tag is not in the correct format.")
                return False

        try: 
            userAccountName = await client.wait_for('message', check=nameIsValid, timeout=30.0)
            confirm_view = ConfirmView(message.author)
            await message.channel.send(f'You entered: {userAccountName.content}. Is this correct?', view=confirm_view)
            await confirm_view.wait()  # Wait for user to interact with the confirmation buttons

            if confirm_view.value is None:
                await message.channel.send("Confirmation timed out. Please try again.")
                return
            if not confirm_view.value:
                await message.channel.send("Please restart the process and enter the correct game name.")
                return
            
            await message.channel.send(f'Thank you! Now, please provide your tagline. (Ex: #NA1)')
            userTagLine = await client.wait_for('message', check=tagIsValid, timeout=30.0)
            confirm_view = ConfirmView(message.author)
            await message.channel.send(f'You entered: {userTagLine.content}. Is this correct?', view=confirm_view)
            await confirm_view.wait()  # Wait for user to interact with the confirmation buttons
            
            if confirm_view.value is None:
                await message.channel.send("Confirmation timed out. Please try again.")
                return
            if not confirm_view.value:
                await message.channel.send("Please restart the process and enter the correct tagline.")
                return

            await message.channel.send(f'Thank you! You entered: {userAccountName.content} and {userTagLine.content}.')

            userTagLine_Cleaned = userTagLine.content.replace("#", "")
            new_account_api_url = account_api_url + userAccountName.content + "/" + userTagLine_Cleaned + "?api_key=" + api_key

            response = requests.get(new_account_api_url)

            if response.status_code == 200:
                await message.channel.send("Account is valid.")
                print(response.json())
                # Extract relevant data from the API response
                api_data = response.json()
                user_data = {
                    "_id": str(message.author.id),
                    "puuid": api_data["puuid"],
                    "account_name": api_data["gameName"],
                    "tag_line": api_data["tagLine"]
                }
                user_info = db["user-data"]

                # # Convert keys to strings
                # user_data_str_keys = {str(key): value for key, value in user_data.items()}

                try:
                    user_info.insert_one(user_data)
                    await message.channel.send("User data successfully stored in the database.")
                except Exception as e:
                    await message.channel.send(f"An error occurred while storing user data: {e}")

            else:
                await message.channel.send("Account is invalid.")
                print(f"API Call failed: {response.status_code} [{response.text}]")


        except asyncio.TimeoutError:
            await message.channel.send("Response took too long. Please try again. (30s)")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")
    
    if message.content.startswith("$profile"):
        user_id = message.author.id
        user_info = db["user-data"]
        user_record = user_info.find_one({"_id": str(user_id)})
        
        if user_record:
            info = user_record
            puuid = info["puuid"]
            summoner_info_api_url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={RIOT_API_KEY}"
            response = requests.get(summoner_info_api_url)

            if response.status_code == 200:
                summoner_data = response.json()
                await message.channel.send(
                    f"Riot Account: {info['account_name']} #{info['tag_line']}\n"
                    f"Summoner Level: {summoner_data['summonerLevel']}"
                )
            else:
                await message.channel.send("Failed to fetch summoner data from Riot API.")
        else:
            await message.channel.send("No information found for your account. Please use $start command to link your Riot account to your Discord account.")


client.run(token)