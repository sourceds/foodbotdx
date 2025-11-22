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

#TODO : integrate with Google Sheets for a more seamless experience,
#       i.e. when you need to update the restaurant database


### setup bot ###
bot = commands.Bot(command_prefix=prefix, intents=discord.Intents.all())

### setup data ###

file_name = os.getenv('DATA')
with open(file_name, mode='r') as file:
    data = list(csv.reader(file, delimiter=','))

# random restaurant selection
# TODO
# 1. add functionality to check for duplicate selections

# LEGACY : supports only food type & restaurant location
def legacy_random_select(type : str, location : str):
    
    def check_criteria(tp : str, loc : str):
        if (tp == any_type and loc == any_location):
            return True
        elif (tp == any_type):
            return (row[2] == loc)
        elif (loc == any_location):
            return (row[1] == tp)
        else:
            return (row[1] == tp and row[2] == loc)
    candidates = []
    for idx in range(0, len(data)):
        row = data[idx]
        if (check_criteria(type, location)):
            candidates.append(idx)
    
    if len(candidates) == 0:
        return -1; #no restaurants matching criteria found

    num = random.randint(0, len(candidates) - 1)
    return candidates[num]

def random_select(params : dict):

    for key, val in params.items():
        if type(val) == int:
            params[key] = str(val)
        
    candidates = []
    for idx in range(0, len(data)):
        row = data[idx]
        flag = True
        for key, val in params.items():
            if key == 1 and val == any_type:
                continue
            elif key == 2 and val == any_location:
                continue
            else:
                if row[key] == val:
                    continue
                else:
                    flag = False
                    break
        if flag == True:
            candidates.append(idx)
    if len(candidates) == 0:
        return -1; #no restaurants matching criteria found

    num = random.randint(0, len(candidates) - 1)
    return candidates[num]

######### Class components #########

class SelectLayoutView(discord.ui.LayoutView):
    def __init__(self, id : int) -> None:
        super().__init__() #pass id

        title = discord.ui.TextDisplay('# ' + '[' + data[id][0] + ']' + '(' + data[id][8] + ')')
        type = discord.ui.TextDisplay('메뉴 : ' + data[id][1])
        location = discord.ui.TextDisplay('위치 : ' + data[id][2])
        detail = discord.ui.TextDisplay('**' + data[id][6] + '**')

        if (data[id][9] != ''):
            media_source = data[id][9]
        else:
            media_source = 'https://img.icons8.com/ios_filled/1200/no-image.jpg' ##TODO : replace later

        gallery = discord.ui.MediaGallery(discord.MediaGalleryItem(media_source))
        container = discord.ui.Container(title, type, location, detail, gallery)
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
            ans = random_select({1 : parameter_type, 2 : parameter_location})
            if (ans != -1):
                await interaction.followup.send(view=SelectLayoutView(ans))
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
            ans = random_select({1 : parameter_type, 2 : parameter_location})
            if (ans != -1):
                await interaction.followup.send(view=SelectLayoutView(ans))
            else:
                await interaction.followup.send("조건을 만족하는 식당이 없습니다.")

# view object for the two select dropdowns
class SelectView(discord.ui.View):
    def __init__(self, *, timeout = 180):
        super().__init__(timeout=timeout)
        self.add_item(SelectType())
        self.add_item(SelectLocation())


# About View

class AboutLayoutView(discord.ui.LayoutView):
    def __init__(self) -> None:
        super().__init__() #pass id

        title = discord.ui.TextDisplay("## 미식봇 DX")
        version =  discord.ui.TextDisplay("DX1.0")
        create1 = discord.ui.TextDisplay("미식봇 DX by srcds")
        create2 = discord.ui.TextDisplay("미식봇 Origial by @Charlie_Lee_Rhee")
        #media_source = 'https://img.icons8.com/ios_filled/1200/no-image.jpg' ##TODO : replace later

        #gallery = discord.ui.MediaGallery(discord.MediaGalleryItem(media_source))
        container = discord.ui.Container(title, version, create1, create2)
        self.add_item(container)


# Help View

class HelpLayoutView(discord.ui.LayoutView):
    def __init__(self) -> None:
        super().__init__() #pass id

        title = discord.ui.TextDisplay("## 미식봇 DX 사용방법")
        cmd1 =  discord.ui.TextDisplay("뭐먹지? : 메뉴와 위치를 정하면 해당 조건에 따라 무작위로 식당을 추천합니다.")
        cmd2 = discord.ui.TextDisplay("다시! : 입력된 조건으로 다시 식당을 추천합니다.")
        cmd3 = discord.ui.TextDisplay("술 : 무작위로 술을 마실 수 있는 식당을 추천합니다")
        #media_source = 'https://img.icons8.com/ios_filled/1200/no-image.jpg' ##TODO : replace later

        #gallery = discord.ui.MediaGallery(discord.MediaGalleryItem(media_source))
        container = discord.ui.Container(title, cmd1, cmd2, cmd3)
        self.add_item(container)


#############################################



@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='what', aliases=['뭐먹지?'])
async def what_to_eat(ctx):
    global parameter_type, parameter_location
    parameter_type = None
    parameter_location = None
    await ctx.send(view=SelectView())

@bot.command(name='retry', aliases=['다시', '다시!'])
async def retry(ctx):
    global parameter_type, parameter_location, last_query_time
    current_query_time = datetime.datetime.now()
    if parameter_type == None and parameter_location == None:
        await ctx.send("뭐먹지? 명령을 먼저 사용해 주세요.")
    elif ((current_query_time - last_query_time).total_seconds() >= 15.0):
        parameter_type = None
        parameter_location = None
    else:
        last_query_time = current_query_time
        result = legacy_random_select(parameter_type, parameter_location)
        if (result == -1):
            await ctx.send("조건을 만족하는 식당이 없습니다.")
        else:
            await ctx.send(view=SelectLayoutView(result))
    
@bot.command(name='alcohol', aliases=['술', '술!'])
async def alcohol(ctx):
    ans = random_select({5 : 1})
    if (ans != -1):
        await ctx.send(view=SelectLayoutView(ans))
    else:
        await ctx.send("조건을 만족하는 식당이 없습니다.")

@bot.command(name='test')
async def test(ctx):
    #await ctx.send(view=LayoutView(random.randint(0, len(data)-1)))
    ans = random_select({1 : '아무거나', 2 : '홍대'})
    if (ans != -1):
        await ctx.send(view=SelectLayoutView(ans))
    else:
        await ctx.send("조건을 만족하는 식당이 없습니다.")

@bot.command(name='about', aliases=['정보'])
async def about(ctx):
    await ctx.send(view=AboutLayoutView())

@bot.command(name='help_menu', aliases=["도와줘"])
async def help_menu(ctx):
    await ctx.send(view=HelpLayoutView())


bot.run(TOKEN)