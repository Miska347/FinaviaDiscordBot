# FINAVIA DISCORD BOT
Made with Python and discord.py
Uses Finavia Public Flights, V0 API

## Features:

- Announce new flights to selected Finavia airport (you can set your own checking interval)
- Send announcement to discord server or user via DM.
- Set notifications (special customizable message) when aircraft type is something else than the airports usual (for example ATRs)

## Commands:

- /set_airport [new airport IATA] - Change airport that bot monitors
- /status - Check selected airport (can be seen also in the bot's status), HTTP-request status and ping
- /refresh - Refresh airport data manually

## Installation: 

- Clone/Download the repository 
    git clone https://github.com/MiskaVou/FinaviaDiscordBot.git
- Create a Discord bot in Discord Developer Portal 
    - Enable all Priviledged Gateway Intents
    - Get your bot token
- Create application at Finavia Developer Portal (Public Flights, V0)
    - Get your app_id and app_key
- Setup .env file
    - Fill up your Discord bot token, Finavia app_id and app_key, Default airport to monitor, Your Discord User ID, Your Discord Server (Guild) ID, Your Discord Channel ID
- Install all the requirements with command:
    pip install -r requirements.txt
- Run the bot with command:
    python3 main.py

