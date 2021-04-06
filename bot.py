import os
import time

import discord
from discord.ext import commands

TOKEN = os.environ.get("TOKEN")
IMAGE_NAME = 'beardedio/terraria'
CONTAINER_NAME = 'terraria'
TERRARIA_FOLDER = os.environ.get('TERRARIA_FOLDER')
TERRARIA_COMMAND_EXIT = 'echo exit | socat EXEC:"docker attach %s",pty STDIN' % CONTAINER_NAME
TERRARIA_COMMAND_MESSAGE = 'echo "say %s" | socat EXEC:"docker attach %s",pty STDIN'
TERRARIA_COMMAND_START = 'docker run --rm -dit -p 7777:7777 --name %s\
                            -v %s:/config \
                            --name=terraria \
                            -e world=%s %s'
TERRARIA_COMMAND_UPDATE = ['docker', 'pull', IMAGE_NAME]
TERRARIA_COMMAND_IS_RUNNING = "docker inspect --format '{{json .State.Running}}' %s" % CONTAINER_NAME

COMMAND_PREFIX = '!'
WORLD_FILENAME = 'Nid_stoique_des_moutons.wld'

bot = discord.ext.commands.Bot(command_prefix=COMMAND_PREFIX)

# Bot commands watch
@bot.command(name='backup', brief="Upload terraria server backup to current channel")
async def backup_terraria(ctx, filename=WORLD_FILENAME):
    await bot_terraria_backup(ctx, filename)

@bot.command(name='start', brief="Start terraria server")
async def start_terraria(ctx, filename=WORLD_FILENAME):
    await bot_terraria_start(ctx, filename)

@bot.command(name='stop', brief="Stop terraria server")
async def stop_terraria(ctx):
    await bot_terraria_stop(ctx)

@bot.command(name='update', brief="Update server version if new available")
async def update_terraria(ctx):
    await bot_terraria_update(ctx)

@bot.command(name='restart', brief="Stop and start the server")
async def update_terraria(ctx, filename=WORLD_FILENAME):
    if await bot_terraria_stop(ctx, restart=True): 
        await bot_terraria_start(ctx, filename, restart=True)

@bot.command(name='status', brief="Print the status of the server")
async def status_terraria(ctx):
    await bot_terraria_status(ctx)

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if str(payload.emoji) != '⬆️':
        return
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    await discord_reaction_loading(message)

    if len(message.attachments) != 1:
        return

    url = message.attachments[0].url
    filename = url.rsplit('/', 1)[-1]
    fileext = filename.rsplit('.', 1)[-1]
    filepath = os.path.join(TERRARIA_FOLDER, filename)

    if not fileext in ['bak', 'bak2', 'wld']:
        return

    try:
        f = open(filepath)
    except IOError:
        if terraria_is_running():
            await discord_reaction_loading(message, False)
            await discord_reaction_fail(message)
            await channel.send("Terraria server is running and file has same name. Stop server before replacing the file" % filename)
    
    await message.attachments[0].save(fp=filepath)

    await discord_reaction_loading(message, False)
    await discord_reaction_done(message)
    await channel.send("Terraria map `%s` uploaded to server :white_check_mark:" % filename)
    
# Bot actions
async def bot_terraria_status(ctx):
    await discord_reaction_loading(ctx.message, False)
    msg = 'Running' if terraria_is_running() else 'Stopped'
    await discord_reaction_done(ctx.message)
    await ctx.send(content="Terraria server status is `%s` :eyes:" % msg)

async def bot_terraria_backup(ctx, filename):
    await discord_reaction_loading(ctx.message)
    path = os.path.join(TERRARIA_FOLDER, filename)
    try:
        f = open(path)
    except IOError:
        await discord_reaction_loading(ctx.message, False)
        await discord_reaction_fail(ctx.message)
        await ctx.send(content="Error while opening file `%s` :question:" % filename)
        return
    
    file = discord.File(path)
    await discord_reaction_loading(ctx.message, False)
    await discord_reaction_done(ctx.message)
    await ctx.send(file=file, content="Terraria map `%s` backup :page_facing_up:" % filename)

async def bot_terraria_start(ctx, filename, restart=False):
    if restart is False:
        await discord_reaction_loading(ctx.message)

    if terraria_is_running():
        await discord_reaction_loading(ctx.message, False)
        await discord_reaction_fail(ctx.message)
        await ctx.send(content="Terraria is already running :exclamation:")
        return False
    terraria_start(filename)
    await discord_reaction_loading(ctx.message, False)
    if not terraria_is_running():
        await discord_reaction_fail(ctx.message)
        return False
    else: 
        await discord_reaction_done(ctx.message)
        if restart:
            await ctx.send(content="Terraria server restarted :green_circle:")
        else:
            await ctx.send(content="Terraria server started :green_circle:")
        return True

async def bot_terraria_stop(ctx, restart=False):
    await discord_reaction_loading(ctx.message)
    if not terraria_is_running():
        await discord_reaction_loading(ctx.message, False)
        await discord_reaction_fail(ctx.message)
        await ctx.send(content="Terraria is not running :exclamation:")
        return False
    
    await terraria_exit()
    terraria_wait_stopped()
    await discord_reaction_loading(ctx.message, False)
    await discord_reaction_done(ctx.message)
    if restart is False:
        await ctx.send(content="Terraria server stopped :red_circle:") 
    return True

async def bot_terraria_update(ctx):
    await discord_reaction_loading(ctx.message)
    
    updated = terraria_update()
    await discord_reaction_loading(ctx.message, False)
    await discord_reaction_done(ctx.message)

    if updated:
        await ctx.send(content="Terraria image server version updated :gear:. Restart server to complete update")
    else: 
        await ctx.send(content="Server already up to date :gear:")

# Discord helpers
async def discord_reaction_loading(message, add=True):
    emoji = '⏳'
    await discord_reaction(message, emoji, add)
    
async def discord_reaction_done(message, add=True):
    emoji = '✅'
    await discord_reaction(message, emoji, add)

async def discord_reaction_fail(message, add=True):
    emoji = '❎'
    await discord_reaction(message, emoji, add)

async def discord_reaction(message, emoji, add=True):
    await message.add_reaction(emoji) if add else await message.remove_reaction(emoji, bot.user)

# Terraria helpers
async def terraria_exit():
    await terraria_send_countdown()
    os.system(TERRARIA_COMMAND_EXIT)

def terraria_start(filename):
    os.system(TERRARIA_COMMAND_START % (CONTAINER_NAME, TERRARIA_FOLDER, filename, IMAGE_NAME))

def terraria_update():
    import docker
    #import code; code.interact(local=dict(globals(), **locals()))
    client = docker.from_env()
    stdout = client.images.pull('%s:latest' % IMAGE_NAME)
    return not('Image is up to date' in stdout)

def terraria_is_running():
    return os.system(TERRARIA_COMMAND_IS_RUNNING) == 0

def terraria_send_message(message):
    os.system(TERRARIA_COMMAND_MESSAGE % (message, CONTAINER_NAME))

def terraria_wait_stopped():
    timeout = time.time() + 30
    while True:
        if terraria_is_running():
            time.sleep(0.5)
        else:
            return True
        if time.time() > timeout:
            return False

async def terraria_send_countdown(seconds=5):
    terraria_send_message('Server will be shutdown in 5 seconds...')
    while(seconds):
        terraria_send_message('%s...' % seconds)
        seconds -= 1
        time.sleep(1)

# DEBUG   
#import code; code.interact(local=dict(globals(), **locals()))
    

# Start bot
bot.run(TOKEN)
