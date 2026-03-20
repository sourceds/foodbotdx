import requests
import sys
import datetime
import json

import convert_date #convert_date.py


cur_date = datetime.date.today() #get today's date
diff = cur_date.isoweekday() #get current week of day as integer

week_start = cur_date - datetime.timedelta(days=diff - 1) #get start day of the week (Monday)
week_end = week_start + datetime.timedelta(days=5) #get end day of the week (Friday)

payload_stDate = convert_date.to_api_date(week_start)
payload_enDate = convert_date.to_api_date(week_end)

MENU_LINK = 'https://www.sogang.ac.kr/api/api/v1/mainKo/menuList'

PAYLOAD = {
    "configId": 1,
    "stDate": payload_stDate,
    "enDate": payload_enDate
}

url = MENU_LINK
payload = PAYLOAD


response = requests.post(url, json=payload)

with open("menu.json", "w") as file:
    json.dump(response.json(), file, ensure_ascii=False, indent=4)
