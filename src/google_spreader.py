import re
import Data_analysis_sheet
from collections import Counter
import json
from operator import itemgetter
from gspread_formatting import *
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def auth_google():
    # returns client
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'client_secret.json',
        ['https://spreadsheets.google.com/feeds'])
    return gspread.authorize(credentials)


def create_wrong_steam_id_sheet(data, client):
    sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1oRedPa92QILDHDlBwsT1EYUpqn92ZuYY7Foc1Muy4Rk')
    sheet.values_clear(
        'wrong Steam_ids!A2:Z1000'
    )
    sheet.values_update(
        'wrong Steam_ids!A2',
        params={'valueInputOption': 'RAW'},
        body={'values': Data_analysis_sheet.wrong_steam_id_list(data)},

    )


def create_switched_team_more_than_once_sheet(data, client):
    sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1oRedPa92QILDHDlBwsT1EYUpqn92ZuYY7Foc1Muy4Rk')
    sheet.values_clear(
         'switched_more_than_once!A2:Z1000'
     )
    list = Data_analysis_sheet.readable_check_if_switched_team_more_than_once(data)
    print(len(list))
    sheet.values_update(
        'switched_more_than_once!A2',  # TODO RENAME
        params={'valueInputOption': 'RAW'},
        body={'values': list},
        # TODO FORMATING
    )

def create_check_lower_div_join_sheet(data,client):
    sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1oRedPa92QILDHDlBwsT1EYUpqn92ZuYY7Foc1Muy4Rk')
    sheet.values_clear(
         'lower_div!A2:Z1000'
    )
    list = Data_analysis_sheet.readable_check_lower_div_join(data)
    print(list)
    sheet.values_update(
        'lower_div!A2',  # TODO RENAME
        params={'valueInputOption': 'RAW'},
        body={'values': list},
        # TODO FORMATING
    )


if __name__ == '__main__':
    client = auth_google()
    # read data
    with open('team_player_data.json', 'r') as file:
        data = json.load(file)

    # sheet with wrong steamids
    create_wrong_steam_id_sheet(data, client)

    create_switched_team_more_than_once_sheet(data, client)
    create_check_lower_div_join_sheet(data, client)

