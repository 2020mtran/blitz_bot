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

async def display_leaderboard(message):
    user_info = db['user-data']
    all_users = user_info.find({}) # Fetch all the documents


    rank_order = [
        "IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"
    ]
    division_order = ["IV", "III", "II", "I"]

    users_data = []
    for user in all_users:
        print(f"User found: {user}")  # Debug: Print each user document
        if "rank" in user:
            print(f"User rank: {user['rank']}")  # Debug: Print rank before split
            rank_info = user["rank"].split()
            print(f"Rank info: {rank_info}")  # Debug: Print rank info after split
        if len(rank_info) == 4:  # Ensure correct split format
            tier = rank_info[0]
            division = rank_info[1]
            lp = int(rank_info[2])
            users_data.append({
            "account_name": user["account_name"],
            "tier": tier,
            "division": division,
            "lp": lp,
            "rank": user["rank"]
        })
        else:
            print(f"Unexpected rank format: {user['rank']}")  # Debug: Print unexpected rank format
    
    print(f"Users with rank data: {users_data}")  # Debug: Print users with rank

    sorted_users = sorted(users_data, key=lambda x: (
        rank_order.index(x["tier"]),
        -division_order.index(x["division"]),
        -x["lp"]
    ))
    print(f"Sorted users: {sorted_users}")  # Debug: Print sorted users

    leaderboard_message = "Leaderboard:\n"
    for idx, user_data in enumerate(sorted_users, start=1):
        leaderboard_message += f"{idx}. {user_data['account_name']} - Rank: {user_data['rank']}\n"

    print(f"Leaderboard message: {leaderboard_message}")  # Debug: Print leaderboard message

    await message.channel.send(leaderboard_message)

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

                # Add summoner's level, summoner id, and account id to the database, & update if exists already
                user_info.update_one(
                    {"_id": str(user_id)},
                    {"$set": {
                        "summoner_level": summoner_data["summonerLevel"],
                        "summoner_id": summoner_data["id"],
                        "account_id": summoner_data["accountId"]
                    }}
                )

                await message.channel.send(
                    f"Riot Account: {info['account_name']} #{info['tag_line']}\n"
                    f"Summoner Level: {summoner_data['summonerLevel']}\n"
                )
                
                summoner_id = summoner_data["id"]
                summoner_rank_api_url = f"https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={RIOT_API_KEY}"
                SR_response = requests.get(summoner_rank_api_url)

                if SR_response.status_code == 200:
                    summoner_rank_data = SR_response.json()

                    if summoner_rank_data:
                        solo_duo_rank = next((entry for entry in summoner_rank_data if entry['queueType'] == 'RANKED_SOLO_5x5'), None)
                        if solo_duo_rank:
                            user_info.update_one(
                                {"_id": str(user_id)},
                                {"$set": {
                                    "rank": f"{solo_duo_rank['tier']} {solo_duo_rank['rank']} {solo_duo_rank['leaguePoints']} LP"
                                }}
                )
                            await message.channel.send(
                                f"Solo/Duo Rank: {solo_duo_rank['tier']} {solo_duo_rank['rank']} {solo_duo_rank['leaguePoints']} LP"
                            )
                    else:
                        await message.channel.send("No ranked solo/duo information found.")
                else:
                    await message.channel.send("No ranked information found.")
            else:
                await message.channel.send("Failed to fetch summoner data from Riot API.")
        else:
            await message.channel.send("No information found for your account. Please use $start command to link your Riot account to your Discord account.")

    if message.content.startswith('$leaderboard'):
        await display_leaderboard(message)  # Call the function to display leaderboard

client.run(token)