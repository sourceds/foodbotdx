import discord
from discord.ext import commands
import dotenv
import os
import csv
import random
import datetime
import sys
import json

import convert_date #convert_date.py

### get discord token ###
dotenv.load_dotenv()
TOKEN = os.getenv('TOKEN')
ADMIN_USERS = os.getenv('ADMIN_USER_IDS').split(',')
### global variables ###
parameter_type = None #selected food type
parameter_location = None #selected location

### CSV INDEX ###
NAME_IDX = 0
CLASS_IDX = 1
LOCATION_IDX = 2
MENU_IDX = 3
ALCOHOL_IDX = 5
DESC_IDX = 6
FAV_IDX = 7
MAP_IDX = 8
IMAGE_IDX = 9

# Indexes for standard foodbot operation (change as needed)

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

def load_data():
    file_name = os.getenv('DATA')
    with open(file_name, mode='r') as file:
        file_data = list(csv.reader(file, delimiter=','))
    file.close()
    return file_data

data = load_data()

def load_menu():
    file_name = os.getenv('MENU')
    with open(file_name, mode='r', encoding='utf-8') as file:
        file_data = json.load(file)
    file.close()
    return file_data

menu = load_menu()

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


# random_select accepts a dictionary that contains the parameters for search
# the dictionary should be structured like this : {rowID : criteria} (i.e. { 1 : '홍대'})
def random_select(params : dict):

    for key, val in params.items():
        if type(val) == int:
            params[key] = str(val)
    # change numeric parameters to string type (for comparison later)
        
    candidates = []
    for idx in range(0, len(data)):
        row = data[idx]
        flag = True
        for key, val in params.items():
            if key == CLASS_IDX and val == any_type:
                continue
            elif key == LOCATION_IDX and val == any_location:
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

class RecommendationView(discord.ui.LayoutView):
    def __init__(self, id : int) -> None:
        super().__init__() #pass id
        title = discord.ui.TextDisplay('## ' + '[' + data[id][NAME_IDX] + ']' + '(' + data[id][MAP_IDX] + ')')
        type = discord.ui.TextDisplay('**메뉴** : ' + data[id][CLASS_IDX] + ' (' + data[id][MENU_IDX] + ')')
        location = discord.ui.TextDisplay('**위치** : ' + data[id][LOCATION_IDX])
        detail = discord.ui.TextDisplay('**' + data[id][6] + '**')


        if (data[id][9] != ''):
            media_source = data[id][IMAGE_IDX]
        else:
            media_source = 'https://raw.githubusercontent.com/sourceds/foodbotdx/refs/heads/main/no_image.jpg'
            ## pulling images from file looks like a chore, so use online media links for now

        gallery = discord.ui.MediaGallery(discord.MediaGalleryItem(media_source))

        info = discord.ui.TextDisplay("-# 이름을 클릭하면 네이버 지도로 이동합니다.")

        favstr = data[id][FAV_IDX]
        if favstr != "":
            favorite = discord.ui.TextDisplay(favstr + "님이 이 식당을 좋아합니다!")
            container = discord.ui.Container(title, type, location, detail, favorite, gallery, info, accent_colour = discord.Colour.blurple())
        else:
            container = discord.ui.Container(title, type, location, detail, gallery, info, accent_colour = discord.Colour.blurple())
        

        ## note: color can be set by accent_colour = Color (Color is an entire discord module class)
        self.add_item(container)

#Haksik Menu Layout

class HaksikView(discord.ui.LayoutView):
    def __init__(self, cur_date : datetime) -> None:
        super().__init__() #pass id

        cur_date_index = cur_date.isoweekday() - 1
        def validate_string(input : str) -> str:
            output = input
            output = output.replace("<br>", "")
            output = output.replace("*", "")
            return output
    
        menu_info = menu["data"]["menuList"][cur_date_index]["menuInfo"]
            
        menustr = ""
        for idx in range(0, 5):
            menustr += '### ' + '<' + menu_info[idx]["category"] + '>' + '\n' + validate_string(menu_info[idx]["menu"]) + '\n'

        title = discord.ui.TextDisplay("# 베르크만스 우정원 (BW관) 식당 메뉴")
        date_range = discord.ui.TextDisplay("## " + convert_date.to_api_date(cur_date))
        data = discord.ui.TextDisplay(menustr)

        container = discord.ui.Container(title, date_range, data, accent_colour = discord.Colour.from_rgb(175, 39, 47)) #set color to cardinal red
        self.add_item(container)


# food type selection
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

        # check if both type and location parameters were entered
        if (parameter_type != None and parameter_location != None):
            last_query_time = datetime.datetime.now()
            ans = random_select({1 : parameter_type, 2 : parameter_location})
            if (ans != -1):
                await interaction.followup.send(view=RecommendationView(ans))
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

        # check if both type and location parameters were entered
        if (parameter_type != None and parameter_location != None):
            last_query_time = datetime.datetime.now()
            ans = random_select({1 : parameter_type, 2 : parameter_location})
            if (ans != -1):
                await interaction.followup.send(view=RecommendationView(ans))
            else:
                await interaction.followup.send("조건을 만족하는 식당이 없습니다.")

# view object for the two select dropdowns
class SelectView(discord.ui.View):
    def __init__(self, *, timeout = 60):
        super().__init__(timeout=timeout)
        self.add_item(SelectType())
        self.add_item(SelectLocation())


# About View

class AboutLayoutView(discord.ui.LayoutView):
    def __init__(self) -> None:
        super().__init__() #pass id

        title = discord.ui.TextDisplay("# 미식봇 DX")
        help = discord.ui.TextDisplay('### 사용법 문의는 "도와줘" 명령을 사용해 주세요!')
        version =  discord.ui.TextDisplay("version 0.1.1 (2026-03)")
        create1 = discord.ui.TextDisplay("미식봇 DX 운영 및 관리: srcds @sourceds")
        create2 = discord.ui.TextDisplay("미식봇 Origial: @Charlie_Lee_Rhee (@Charlie_Lee_Rhee)")
        container = discord.ui.Container(title, help, version, create1, create2)
        self.add_item(container)


# Help View

class HelpLayoutView(discord.ui.LayoutView):
    def __init__(self) -> None:
        super().__init__() #pass id

        title = discord.ui.TextDisplay("# 미식봇 사용방법")
        header1 = discord.ui.TextDisplay("## 기본 검색")
        cmd1 =  discord.ui.TextDisplay("뭐먹지? : 메뉴와 위치를 입력하면 해당 조건에 따라 무작위로 식당을 추천합니다.")
        cmd2 = discord.ui.TextDisplay("다시! : 입력된 조건으로 다시 식당을 추천합니다.")
        header2 = discord.ui.TextDisplay("## 상세 검색")
        cmd3 = discord.ui.TextDisplay("술 : 술을 마실 수 있는 식당을 추천합니다")
        cmd4 = discord.ui.TextDisplay("[메뉴]/[지역] : 원하는 지역의 식당이나 메뉴에 따라 빠르게 검색할 수 있습니다.")
        cmd5 = discord.ui.TextDisplay("학식 : 오늘의 베르크만스 우정원(BW관) 메뉴를 표시합니다.")
        header3 = discord.ui.TextDisplay("## 유틸리티 (Admin Only)")
        cmd6 = discord.ui.TextDisplay("재시작 : 현재 미식봇 Instance를 재시작합니다.")
        cmd7 = discord.ui.TextDisplay("갱신 : 데이터를 다시 로드합니다.")
        cmd8 = discord.ui.TextDisplay('### ' + '[' + "GitHub 리포지토리" + ']' + '(' + 'https://github.com/sourceds/foodbotdx' + ')')
        container = discord.ui.Container(title, header1, cmd1, cmd2, header2, cmd3, cmd4, cmd5, header3, cmd6, cmd7, cmd8)
        self.add_item(container)
        

        


#############################################



@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!') # type: ignore

@bot.command(name='hi', aliases=["ㅎㅇ", "안녕"])
async def hi(ctx):
    await ctx.send("안뇽!")

@bot.command(name='what', aliases=['뭐먹지?', '뭐먹지!', '뭐먹지'])
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
    elif ((current_query_time - last_query_time).total_seconds() >= 30.0):
        parameter_type = None
        parameter_location = None
        #reset
    else:
        last_query_time = current_query_time
        result = random_select({1 : parameter_type, 2 : parameter_location})
        if (result == -1):
            await ctx.send("조건을 만족하는 식당이 없습니다.")
        else:
            await ctx.send(view=RecommendationView(result))
    

@bot.command(name='alcohol', aliases=['술', '술!'])
async def alcohol(ctx):
    ans = random_select({5 : 1})
    if (ans != -1):
        await ctx.send(view=RecommendationView(ans))
    else:
        await ctx.send("조건을 만족하는 식당이 없습니다.")


## region-based search ##

@bot.command(name='sogang', aliases=['서강', '서강!'])
async def sogang(ctx):
    ans = random_select({2 : '서강'})
    if (ans != -1):
        await ctx.send(view=RecommendationView(ans))
    else:
        await ctx.send("조건을 만족하는 식당이 없습니다.")

@bot.command(name='hongdae', aliases=['홍대', '홍대!'])
async def hongdae(ctx):
    ans = random_select({2 : '홍대'})
    if (ans != -1):
        await ctx.send(view=RecommendationView(ans))
    else:
        await ctx.send("조건을 만족하는 식당이 없습니다.")

@bot.command(name='sinchon', aliases=['신촌', '신촌!'])
async def sinchon(ctx):
    ans = random_select({2 : '신촌'})
    if (ans != -1):
        await ctx.send(view=RecommendationView(ans))
    else:
        await ctx.send("조건을 만족하는 식당이 없습니다.")


## menu-based search ##

@bot.command(name='japanese', aliases=['일식', '일식!'])
async def japanese(ctx):
    ans = random_select({1 : '일식'})
    if (ans != -1):
        await ctx.send(view=RecommendationView(ans))
    else:
        await ctx.send("조건을 만족하는 식당이 없습니다.")

@bot.command(name='korean', aliases=['한식', '한식!'])
async def korean(ctx):
    ans = random_select({1 : '한식'})
    if (ans != -1):
        await ctx.send(view=RecommendationView(ans))
    else:
        await ctx.send("조건을 만족하는 식당이 없습니다.")

@bot.command(name='chinese', aliases=['중식', '중식!'])
async def chinese(ctx):
    ans = random_select({1 : '중식'})
    if (ans != -1):
        await ctx.send(view=RecommendationView(ans))
    else:
        await ctx.send("조건을 만족하는 식당이 없습니다.")

@bot.command(name='western', aliases=['양식', '양식!'])
async def western(ctx):
    ans = random_select({1 : '양식'})
    if (ans != -1):
        await ctx.send(view=RecommendationView(ans))
    else:
        await ctx.send("조건을 만족하는 식당이 없습니다.")


@bot.command(name='haksik', aliases=["학식"])
async def haksik(ctx):
    cur_date = datetime.date.today()
    cur_date_index = cur_date.isoweekday() - 1

    try:
        if (cur_date_index > 4):
            await ctx.send("오늘의 학식 정보가 없습니다.")
        else:
            await ctx.send(view=HaksikView(cur_date))

    except (KeyError):
        await ctx.send("내부 오류가 발생했습니다. (KeyError)")


## Help commands ##

@bot.command(name='about', aliases=['정보'])
async def about(ctx):
    await ctx.send(view=AboutLayoutView())


@bot.command(name='help_menu', aliases=["도와줘"])
async def help_menu(ctx):
    await ctx.send(view=HelpLayoutView())

@bot.command(name='index_search', aliases=['인덱스'])
async def index_search(ctx, arg):
    print(f"{arg}, {arg.isdigit()}, {int(arg)}")
    if (arg.isdigit()):
        idx = int(arg)
        if (idx >= len(data) or idx < 1):
            await ctx.send("해당 정보가 존재하지 않습니다. (범위 : 1 ~ " + str(len(data)) + ")")
        else:
            await ctx.send(view=RecommendationView(idx))
    else:
        await ctx.send("입력은 1 이상의 정수여야 합니다.")

##TODO : get menu from before-it-melts notion

### Utility Functions ###

@bot.command(name='update_data', aliases=['갱신'])
async def update_data(ctx):
    await ctx.send("Loading restaurant data...")
    load_data()
    if data is False:
        await ctx.send("Error: Could not update restaurant data")
    else:
        await ctx.send("Successfully updated restaurant data")


@bot.command(name='restart', aliases=['재시작'])
async def restart(ctx):
    if str(ctx.author.id) in ADMIN_USERS:
        await ctx.send("Restarting FoodBot...")
        os.execv(sys.executable, ['python3'] + sys.argv)
    else:
        await ctx.send("권한이 없습니다.")

bot.run(TOKEN)