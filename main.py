import discord
from discord.ext import commands
import dotenv
import os
import csv
import random
import threading
import datetime

### TODO ###

# - find a way to clear parameters after a certain amout of time has passed without input
############
### get discord token ###
dotenv.load_dotenv()
TOKEN = os.getenv('TOKEN')


### global variables ###

parameter_type = None #selected food type
parameter_location = None #selected location

any_type = '아무거나'
any_location = '아무데나'
list_type = [any_type, '한식', '중식', '일식', '양식', '간식', '기타']
list_location = [any_location, '신촌', '홍대', '합정', '마포', '서강']
prefix = '미식봇! '

last_query_time = None

### setup bot ###
bot = commands.Bot(command_prefix=prefix, intents=discord.Intents.all())


### setup data ###

#TODO : integrate with Google Sheets for a more seamless experience,
#       i.e. when you need to update the restaurant database

file_name = os.getenv('DATA')
with open(file_name, mode='r') as file:
    data = list(csv.reader(file, delimiter=','))

# input wait function


# random restaurant selection
# TODO
# 1. add functionality to check for duplicate selections
def random_select(type : str, location : str):
    
    def check_criteria(type : str, location : str):
        if (type == any_type and location == any_location):
            return True
        elif (type == any_type):
            return row[2] == location
        else:
            return row[1] == type

    candidates = []
    for idx in range(0, len(data)):
        row = data[idx]
        if (check_criteria(type, location)):
            candidates.append(idx)
    
    if len(candidates) == 0:
        return -1; #no restaurants matching criteria found

    num = random.randint(0, len(candidates) - 1)
    return candidates[num]

######### Class components #########
class LayoutView(discord.ui.LayoutView):
    def __init__(self, id : int) -> None:
        super().__init__() #pass id
    
        #self.thumbnail = discord.ui.Thumbnail(media='https://maimai.sega.jp/storage/area/region/kawaii2/icon/01.png')

        title = discord.ui.TextDisplay('**' + data[id][0] + '**')
        detail = discord.ui.TextDisplay(data[id][6])

        if (data[id][9] != ''):
            media_source = data[id][9]
        else:
            media_source = 'https://i.pinimg.com/736x/f9/c6/24/f9c624561595995676ffec4d360257e7.jpg'

        gallery = discord.ui.MediaGallery(discord.MediaGalleryItem(media_source))
        container = discord.ui.Container(title, detail, gallery)
        self.add_item(container)


class SelectType(discord.ui.Select):
    def __init__(self):
        options = []
        for type in list_type:
            options.append(discord.SelectOption(label=type, description=type))
        super().__init__(placeholder="음식 분류를 선택해 주세요",max_values=1,min_values=1,options=options)
    async def callback(self, interaction: discord.Interaction):
        global parameter_type, last_query_time
        parameter_type = self.values[0]
        await interaction.response.send_message(content=f"{parameter_type}을 선택하셨습니다.")
        if (parameter_type != None and parameter_location != None):
            #print(f"Both parameters entered : {parameter_type} and {parameter_location}") -> currently here for testing purposes
            last_query_time = datetime.datetime.now()
            ans = random_select(parameter_type, parameter_location)
            if (ans != -1):
                await interaction.followup.send(view=LayoutView(ans))
            else:
                await interaction.followup.send("조건을 만족하는 식당이 없습니다.")


#location selection
class SelectLocation(discord.ui.Select):
    def __init__(self):
        options = []
        for location in list_location:
            options.append(discord.SelectOption(label=location, description=location))
        super().__init__(placeholder="식당 위치를 선택해 주세요",max_values=1,min_values=1,options=options)
    async def callback(self, interaction: discord.Interaction):
        global parameter_location, last_query_time
        parameter_location = self.values[0]
        await interaction.response.send_message(content=f"{parameter_location}을 선택하셨습니다.")
        if (parameter_type != None and parameter_location != None):
            #print(f"Both parameters entered : {parameter_type} and {parameter_location}") -> currently here for testing purposes
            last_query_time = datetime.datetime.now()
            ans = random_select(parameter_type, parameter_location)
            if (ans != -1):
                await interaction.followup.send(view=LayoutView(ans))
            else:
                await interaction.followup.send("조건을 만족하는 식당이 없습니다.")

# view object for the two select dropdowns
class SelectView(discord.ui.View):
    def __init__(self, *, timeout = 180):
        super().__init__(timeout=timeout)
        self.add_item(SelectType())
        self.add_item(SelectLocation())


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='뭐먹지?')
async def what_to_eat(ctx):
    global parameter_type, parameter_location
    parameter_type = None
    parameter_location = None
    await ctx.send(view=SelectView())

@bot.command(name='test')
async def test(ctx):
    await ctx.send(view=LayoutView(random.randint(0, len(data)-1)))

@bot.command(name='다시!')
async def retry(ctx):
    global parameter_type, parameter_location, last_query_time
    current_query_time = datetime.datetime.now()
    if parameter_type == None and parameter_location == None:
        await ctx.send("뭐먹지? 명령을 먼저 사용해 주세요.")
    elif ((current_query_time - last_query_time).total_seconds() >= 15.0):
        parameter_type = None
        parameter_location = None
        await ctx.send("timeout due to inactivity")
    else:
        last_query_time = current_query_time
        await ctx.send(view=LayoutView(random_select(parameter_type, parameter_location)))
    
bot.run(TOKEN)
