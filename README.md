# FINAVIA DISCORD BOT
Made with Python and discord.py
Uses Finavia Public Flights, V0 API

## Features:

- Announce new flights to selected Finavia airport (you can set your own checking interval)
- Send announcement to discord server or user via DM. (Can be toggled ON/OFF)
- Set notifications (special customizable message) when aircraft type is something else than the airports usual (for example ATRs) (Can be toggled ON/OFF)
- Send message only about flights that haven't been announced before. (Can be toggled ON/OFF)
- Setting changes made with commands are saved to config file (.env)

## Commands:

- /set_airport [new airport IATA] - Change airport that bot monitors
- /status - Check selected airport (can be seen also in the bot's status), HTTP-request status and ping
- /refresh - Refresh airport data manually
- /clear - Clear flights history. Useful if you get messages only about flights that haven't been announced before, so you can get the full flights list with using first /clear and then /refresh
- /only_new_flights - Send message only about flights that haven't been announced before or always show all flights that are coming (True = Shows only new flights / False = Shows all flights)

## Installation: 

- Clone/Download the repository 
```
    git clone https://github.com/MiskaVou/FinaviaDiscordBot.git
```
- Create a Discord bot in Discord Developer Portal 
    - Enable all Priviledged Gateway Intents
    - Get your bot token
- Create application at Finavia Developer Portal (Public Flights, V0)
    - Get your app_id and app_key
- Setup .env file
    - Fill up your Discord bot token, Finavia app_id and app_key, Default airport to monitor, Your Discord User ID, Your Discord Server (Guild) ID, Your Discord Channel ID
- Install all the requirements with command:
```
    pip install -r requirements.txt
```
- Run the bot with command:
```
    python3 main.py
```

