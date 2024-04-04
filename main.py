import discord
import requests
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv
from dotenv import set_key
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import pytz
from datetime import datetime

load_dotenv()

your_discord_id = int(os.getenv("YOUR_DISCORD_ID"))
your_channel_id = int(os.getenv("YOUR_CHANNEL_ID"))
your_guild_id = int(os.getenv("YOUR_GUILD_ID"))
app_id = os.getenv("APP_ID")
api_key = os.getenv("API_KEY")
airport_code = os.getenv("AIRPORT_CODE")
base_api_url = os.getenv("BASE_API_URL")

notify_special = os.getenv("NOTIFY_SPECIAL").lower() == "true"
not_special_ac = os.getenv("NOT_SPECIAL_AC")

show_only_new_flights = os.getenv("SHOW_ONLY_NEW_FLIGHTS").lower() == "true"

check_interval = os.getenv("CHECK_INTERVAL")


previous_data = {'departures': [], 'arrivals': []}

intents = discord.Intents.all()
intents.messages = True
intents.guilds = True

client = commands.Bot(command_prefix='!', intents = intents)

@client.tree.command(name='set_airport', description='Change airport to monitor')
@app_commands.describe(new_airport_code="New airport (IATA)")
async def set_airport(ctx: commands.Context, new_airport_code: str):

    await ctx.response.defer(ephemeral=True)
    
    # Päivitetään airport code ja api url kaikkialle
    global airport_code
    airport_code = new_airport_code
    global api_url
    api_url = f"{base_api_url}{airport_code}"

    # Vastaus slash-komennolle
    await ctx.followup.send(f'## :gear: Setting changed and updated to config: \nSelected airport: **{new_airport_code}**')

    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{airport_code} lentoasema"))

    set_key('.env', 'AIRPORT_CODE', new_airport_code)


@client.tree.command(name='only_new_flights', description='Send message only about flights that havent been announced before.')
@app_commands.describe(only_new_flights="True / False")
async def only_new_flights(ctx: commands.Context, only_new_flights: str):
    await ctx.response.defer(ephemeral=True)
    
    global show_only_new_flights
    show_only_new_flights = only_new_flights.lower() == "true"

    await ctx.followup.send(f'## :gear: Setting changed and updated to config: \nSend message only about flights that havent been announced before: **{only_new_flights}**')

    set_key('.env', 'SHOW_ONLY_NEW_FLIGHTS', only_new_flights.lower())



@client.tree.command(name='notify_special', description='Send message only about flights that havent been announced before.')
@app_commands.describe(notify_special_ac="True / False")
async def notify_specialcommand(ctx: commands.Context, notify_special_ac: str):
    await ctx.response.defer(ephemeral=True)
    
    global notify_special
    notify_special = notify_special_ac.lower() == "true"

    await ctx.followup.send(f'## :gear: Setting changed and updated to config: \nSend notification about special aircrafts: **{notify_special_ac}**')

    set_key('.env', 'NOTIFY_SPECIAL', notify_special_ac.lower())



@client.tree.command(name="status", description='Shows selected airport, HTTP-request status, ping')
async def status(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    response = requests.get(api_url, headers=headers)
    response.raise_for_status()

    # Tulosta HTTP-pyynnön tilakoodi ja vastaus tekstinä
    print(f"HTTP-pyynnön tilakoodi: {response.status_code}")
    print(response.text)

    await interaction.followup.send(f'Selected airport: {airport_code}\nHTTP-request response: {response.status_code}\nPing: {round(client.latency, 1)}')


@client.tree.command(name="refresh", description='Refresh data')
async def refresh(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    await send_flight_data()

    await interaction.followup.send(f'Refreshed.')


@client.tree.command(name="previous", description='See previous data')
async def previous(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    await interaction.followup.send(f'{previous_data}')


@client.tree.command(name="clear", description='Clear data')
async def clear(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    global previous_data
    previous_data = []

    await interaction.followup.send(f'Cleared.')

# Aseta API
api_url = f"{base_api_url}{airport_code}"

headers = {
    'Accept': 'application/xml',
    'app_id': app_id,
    'app_key': api_key
}


# Funktio tiedon hakemiseksi API:sta
def get_flight_data():
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()

        # Tulosta HTTP-pyynnön tilakoodi ja vastaus tekstinä
        print(f"HTTP-pyynnön tilakoodi: {response.status_code}")
        print(response.text)

        # Parsi XML-vastaus
        root = ET.fromstring(response.text)

        # Ota huomioon XML-namespace
        ns = {'flights': 'http://www.finavia.fi/FlightsService.xsd'}

        # Etsi departure- ja arrival-lennot erikseen
        departure_flights = root.findall('.//flights:dep/flights:body/flights:flight', namespaces=ns)
        arrival_flights = root.findall('.//flights:arr/flights:body/flights:flight', namespaces=ns)

        # Valitse tarvittavat tiedot departure-lennoista
        departure_data = []
        for flight in departure_flights:
            fltnr = flight.find('flights:fltnr', namespaces=ns).text
            sdt = flight.find('flights:sdt', namespaces=ns).text
            callsign = flight.find('flights:callsign', namespaces=ns).text
            acreg = flight.find('flights:acreg', namespaces=ns).text
            actype = flight.find('flights:actype', namespaces=ns).text
            h_apt = flight.find('flights:h_apt', namespaces=ns).text
            route_1 = flight.find('flights:route_1', namespaces=ns).text

            # Muuta aika timestamp-muotoon Suomen aikavyöhykkeelle ja UTC +0
            sdt_timestamp_utc = datetime.fromisoformat(sdt[:-1])  # Poista 'Z' lopusta
            sdt_timestamp_utc = sdt_timestamp_utc.replace(tzinfo=pytz.utc)
            sdt_timestamp_str_local = f"<t:{int(sdt_timestamp_utc.timestamp())}:f> <t:{int(sdt_timestamp_utc.timestamp())}:R>"

            departure_data.append({
                'fltnr': fltnr,
                'sdt_timestamp_str_local': sdt_timestamp_str_local,
                'callsign': callsign,
                'acreg': acreg,
                'actype': actype,
                'h_apt': h_apt,
                'route_1': route_1
            })

        # Valitse tarvittavat tiedot arrival-lennoista
        arrival_data = []
        for flight in arrival_flights:
            fltnr = flight.find('flights:fltnr', namespaces=ns).text
            sdt = flight.find('flights:sdt', namespaces=ns).text
            callsign = flight.find('flights:callsign', namespaces=ns).text
            acreg = flight.find('flights:acreg', namespaces=ns).text
            actype = flight.find('flights:actype', namespaces=ns).text
            h_apt = flight.find('flights:h_apt', namespaces=ns).text
            route_1 = flight.find('flights:route_1', namespaces=ns).text

            # Muuta aika timestamp-muotoon Suomen aikavyöhykkeelle ja UTC +0
            sdt_timestamp_utc = datetime.fromisoformat(sdt[:-1])  # Poista 'Z' lopusta
            sdt_timestamp_utc = sdt_timestamp_utc.replace(tzinfo=pytz.utc)
            sdt_timestamp_str_local = f"<t:{int(sdt_timestamp_utc.timestamp())}:f> <t:{int(sdt_timestamp_utc.timestamp())}:R>"

            arrival_data.append({
                'fltnr': fltnr,
                'sdt_timestamp_str_local': sdt_timestamp_str_local,
                'callsign': callsign,
                'acreg': acreg,
                'actype': actype,
                'h_apt': h_apt,
                'route_1': route_1
            })

        return departure_data, arrival_data

    except requests.exceptions.RequestException as err:
        print(f"Virhe HTTP-pyynnössä: {err}")
        return None, None
    except Exception as e:
        print(f"Jokin meni pieleen: {e}")
        return None, None


@tasks.loop(minutes=float(check_interval))
async def send_flight_data():
    global previous_data

    departure_data, arrival_data = get_flight_data()
    message_no_data = f"No data found for the selected airport ({airport_code}) (no traffic?)"

    if departure_data or arrival_data:
        # Create an empty embed
        embed = discord.Embed(title=f"New flights ({airport_code})", color=0x2e5fa9)
        embed.set_footer(text=f"{airport_code} Airport | Finland Time | Data from Finavia")

        # Check if you want to show all flights always
        if show_only_new_flights:
            new_departure_flights = [message for message in departure_data if message not in previous_data['departures']]
            new_arrival_flights = [message for message in arrival_data if message not in previous_data['arrivals']]
        else:
            new_departure_flights = departure_data
            new_arrival_flights = arrival_data
            
        if not new_departure_flights and not new_arrival_flights:
            # No new flights, update the embed accordingly
            embed.description = "**No new flights found.**"
        else:
            if new_arrival_flights:
                # Add "ARRIVALS" section to the embed
                embed.add_field(name="ARRIVALS:", value="\u200b", inline=False)
                # Add arrival flight information to the embed under "ARRIVALS" section
                for message in new_arrival_flights:
                    embed.add_field(
                        name=f"🛬 {message['fltnr']} / {message['callsign']}",
                        value=f"Route: {message['route_1']} -> {message['h_apt']}\nTime: {message['sdt_timestamp_str_local']}\nA/C: {message['actype']} ({message['acreg']})",
                        inline=False
                    )

            if new_departure_flights:
                # Add "DEPARTURES" section to the embed
                embed.add_field(name="DEPARTURES:", value="\u200b", inline=False)
                # Add departure flight information to the embed under "DEPARTURES" section
                for message in new_departure_flights:
                    embed.add_field(
                        name=f"🛫 {message['fltnr']} / {message['callsign']}",
                        value=f"Route: {message['h_apt']} -> {message['route_1']}\nTime: {message['sdt_timestamp_str_local']}\nA/C: {message['actype']} ({message['acreg']})",
                        inline=False
                    )

        # Save the new state (data)
        previous_data['departures'] = departure_data
        previous_data['arrivals'] = arrival_data

        # Add special aircrafts notification
        if (new_departure_flights or new_arrival_flights) and notify_special is True and any(message['actype'] not in not_special_ac for message in departure_data + arrival_data):
            notificationmessage_user = f"## Some special aircrafts coming! <@{your_discord_id}> \n*You have set notifications when aircraft type is something else than* `{not_special_ac}`"
            notificationmessage_server = f"## Some special aircrafts coming! @everyone \n*You have set notifications when aircraft type is something else than* `{not_special_ac}`"

            notificationmessage_user = notificationmessage_user.replace("[", "").replace("]", "").replace("'", "")
            notificationmessage_server = notificationmessage_server.replace("[", "").replace("]", "").replace("'", "")

            user = await client.fetch_user(your_discord_id)
            await user.send(notificationmessage_user)

            channel = client.get_channel(your_channel_id)
            await channel.send(notificationmessage_server)

        # Send the embed as a private message
        user = await client.fetch_user(your_discord_id)
        await user.send(embed=embed)

        # Get the server + channel and send the embed to the channel as well
        channel = client.get_channel(your_channel_id)
        await channel.send(embed=embed)
    else:
        print("Could not send data because API request failed or no data found. Sending error message")
        # Send a message as a private message
        user = await client.fetch_user(your_discord_id)
        await user.send(message_no_data)

        # Get the channel and send the message to the channel as well
        channel = client.get_channel(your_channel_id)
        await channel.send(message_no_data)



#    # Hae kuvan URL rekisteritunnuksen perusteella
#    registration = flight_data['acreg']
#    image_url = await get_aircraft_image(registration)
#    if image_url:
#        embed.set_image(url=image_url)
#
#    return embed

#async def get_aircraft_image(registration):
#    registration_new = "OH-ATP"
#    api_url = f"https://api.planespotters.net/pub/photos/reg/{registration_new}"
#    
#    try:
#        response = requests.get(api_url)
#        response.raise_for_status()
#
#        data = response.json()
#        if data and "photos" in data and data["photos"]:
#            # Palauta ensimmäisen kuvan URL
#            first_photo = data["photos"][0]
#            thumbnail_large = first_photo["thumbnail_large"]["src"]
#            return thumbnail_large
#
#    except requests.exceptions.RequestException as err:
#        print(f"Virhe kuvan hakemisessa: {err}")
#
#    return None

# Käynnistä ajastin
@client.event
async def on_ready():
    print(f'Kirjauduttu sisään: {client.user}')

    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{airport_code} lentoasema"))

    synced = await client.tree.sync()

    print(f"Synced {len(synced)} command(s)")

    send_flight_data.start()

# Käynnistä botti
client.run(os.getenv("BOT_TOKEN"))
