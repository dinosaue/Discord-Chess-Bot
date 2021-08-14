import os 

import discord
import discord_slash
import pandas as pd

model_params = pd.read_csv("/Users/austinliu/Downloads/Discord-Chess-Bot-master/data/model_params_20210805.csv")

from discord.ext import commands
from calcs import expected_date
from calcs import get_predicted_date 
from calcs import get_prob_success
from calcs import get_predictor_values
from calcs import process_rating_history
from calcs import score 

from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
# GUILD = os.getenv('DISCORD_GUILD')

# client = discord.Client()

# @client.event
# async def on_ready():
#     guild = discord.utils.get(client.guilds, name=GUILD)
#     print(
#         f'{client.user} is connected to the following guild:\n'
#         f'{guild.name}(id: {guild.id})'
#     )

bot = commands.Bot(command_prefix='!', help_command=None) 
@bot.command(name="whenrating")
async def whenrating(ctx, name, rating, variant="Rapid"):
  if not rating.isnumeric():
    await ctx.send("Error: Rating must be an integer.")
    return
  (prob_success,predicted_date) = score(name,int(rating),variant,model_params)
  print ("test1")
  print ("prob success: ", prob_success)
  print ("predicted date: ", predicted_date)
  await ctx.send(f"{name} has a {prob_success} chance of reaching a {variant} rating of {rating} within the next 2 years. If {name} succeeds, I predict the rating will be achieved around {predicted_date}.")  
# except:
  if predicted_date == None:
    await ctx.send(f"Error: Not enough rating history for **{variant}** for **{name}**!")
    print ("test")
    return
  elif predicted_date == -1:
    await ctx.send(f"Error: No lichess user with name **{name}**!")
    return
  await ctx.send(f'{name} can expect to have a {variant} rating of {rating} on {date.strftime("%b %d, %Y")}.')


# slash = discord_slash.SlashCommand(bot, sync_commands=True)
# @slash.slash(name="whenrating", description="Enter a lichess username and a rating to see the expected time when that rating will be achieved.")
# async def _whenrating(ctx, name, rating, variant="Rapid"):
#   await whenrating(ctx, name, rating, variant)

bot.run(TOKEN)
