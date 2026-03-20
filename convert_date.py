import datetime

def to_api_date(param : datetime) -> str:
    str_year = str(param.year)
    str_month = str(param.month)
    str_day = str(param.day)

    if (param.month < 10):
        str_month = '0' + str_month
    
    if (param.day < 10):
        str_day = '0' + str_day
    
    api_date = str_year + '.' + str_month + '.' + str_day
    return api_date