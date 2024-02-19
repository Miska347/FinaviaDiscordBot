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

usual_aircrafts = os.getenv("USUAL_AIRCRAFTS")

show_always_all_flights = os.getenv("SHOW_ALWAYS_ALL_FLIGHTS")


previous_data = []

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


@client.tree.command(name='showall', description='Send message only about flights that havent been announced before.')
@app_commands.describe(showall="True / False")
async def showall(ctx: commands.Context, showall: str):

    await ctx.response.defer(ephemeral=True)
    
    # Päivitetään airport code ja api url kaikkialle
    global show_always_all_flights
    show_always_all_flights = showall

    # Vastaus slash-komennolle
    await ctx.followup.send(f'## :gear: Setting changed and updated to config: \nSend message only about flights that havent been announced before: **{showall}**')

    set_key('.env', 'SHOW_ALWAYS_ALL_FLIGHTS', showall)


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

        # Etsi departure- ja arrival-lennot
        departure_flights = root.findall('.//flights:dep/flights:body/flights:flight', namespaces=ns)
        arrival_flights = root.findall('.//flights:arr/flights:body/flights:flight', namespaces=ns)

        # Yhdistä lennot yhteen listalle
        all_flights = departure_flights + arrival_flights

        # Valitse tarvittavat tiedot
        flights = []
        for flight in all_flights:
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
            sdt_timestamp_str_utc = f"<t:{int(sdt_timestamp_utc.timestamp())}:f> <t:{int(sdt_timestamp_utc.timestamp())}:R>"

            sdt_timestamp_local = sdt_timestamp_utc.astimezone(pytz.timezone('Europe/Helsinki'))
            sdt_timestamp_str_local = f"<t:{int(sdt_timestamp_local.timestamp())}:f> <t:{int(sdt_timestamp_local.timestamp())}:R>"

            # Tarkista, onko lento <dep> vai <arr>
            is_departure = flight.tag.endswith('dep')

            # Muodosta viesti
            if is_departure:
                message = f"Lento: {fltnr} / {callsign}. Reitti: {h_apt} -> {route_1} (Saapuu: {sdt_timestamp_str_local} UTC+2) Kone: {actype} ({acreg})"
            else:
                message = f"Lento: {fltnr} / {callsign}. Reitti: {route_1} -> {h_apt} (Lähtee: {sdt_timestamp_str_local} UTC+2) Kone: {actype} ({acreg})"


            flights.append({
            'fltnr': fltnr,
            'sdt_timestamp_str_local': sdt_timestamp_str_local,
            'callsign': callsign,
            'acreg': acreg,
            'actype': actype,
            'h_apt': h_apt,
            'route_1': route_1
    })

        return flights

    except requests.exceptions.RequestException as err:
        print(f"Virhe HTTP-pyynnössä: {err}")
        return None
    except Exception as e:
        print(f"Jokin meni pieleen: {e}")
        return None


# Ajastin hakee tiedot ja lähettää ne yksityisviestinä Discordissa ja kanavalle
@tasks.loop(hours=1)
async def send_flight_data():
    global previous_data

    data = get_flight_data()
    message_no_data = f"No data found for the selected airport ({airport_code}) (no traffic?)"
    print("Data:", data)

    if data:
        # Create an empty embed
        embed = discord.Embed(title=f"New flights ({airport_code})", color=0x00ff00)
        embed.set_footer(text=f"{airport_code} Airport | Data from Finavia")

        # Check if you want to show all flights always
        if show_always_all_flights:
            new_flights = data
        else:
            # Compare new data with previous data
            new_flights = [message for message in data if message not in previous_data]

        if not new_flights:
            # No new flights, update the embed accordingly
            embed.description = "**No new flights found.**"
        else:
            for message in new_flights:
                # Add flight information to the embed
                embed.add_field(
                    name=f"Flight: {message['fltnr']} / {message['callsign']}",
                    value=f"Route: {message['h_apt']} -> {message['route_1']}\nTime: {message['sdt_timestamp_str_local']} UTC+2\nA/C: {message['actype']} ({message['acreg']})",
                    inline=False
                )

        # Save the new state (data)
        previous_data = data

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

async def create_flight_embed(flight_data):
    embed = discord.Embed(color=0x00ff00)

    # Lisää kentät embediin
    embed.add_field(name="Flight", value=f"{flight_data['fltnr']} / {flight_data['callsign']}", inline=False)
    embed.add_field(name="Route", value=f"{flight_data['h_apt']} -> {flight_data['route_1']}", inline=False)
    embed.add_field(name="Time", value=f"{flight_data['sdt_timestamp_str_local']} UTC+2", inline=False)
    embed.add_field(name="A/C", value=f"{flight_data['actype']} ({flight_data['acreg']})", inline=False)

    embed.set_footer(text=f"{airport_code} Airport | Data from Finavia")


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
