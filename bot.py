import discord
from discord.ext import commands

import os

bot = discord.ext.commands.Bot(command_prefix='!');
    
@bot.command(name='backup', brief="Upload terraria server backup to #terraria")
async def backup_terraria(ctx):
    file = discord.File("Nid_stoique_des_moutons.wld")
    await ctx.send(file=file, content="Backup")
                        
bot.run(os.environ.get("TOKEN"))
