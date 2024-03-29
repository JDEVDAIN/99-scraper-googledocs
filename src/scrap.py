# coding=utf-8
import requests
import bs4
import copy
from datetime import datetime
import CONFIG


def get_divlinks_dic_from_leaguepage(link):
    """
    Gets run first. Gets all Division links.
    :param link: 99Damage Season link
    :return: Dic with all Divisions and links.
    """
    # connect
    url = link
    # TODO remove generate_user_agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:46.0) Gecko/20100101 Firefox/46.0'}
    # TODO: is connection with own ip
    website = requests.get(url, headers=headers)
    website.raise_for_status()
    # get html
    league_soup = bs4.BeautifulSoup(website.text, features="lxml")

    divlinks_dic = {}

    # div 1
    leagueDivOne_element = league_soup.select('.league_overview_box .league_table .title')
    # [1:] needed bc of \n
    divlinks_dic[leagueDivOne_element[0].text[1:-1]] = {'link': leagueDivOne_element[0].a['href']}

    # all divs, start div2
    league_element = league_soup.select('.league_overview_box .groups li')
    for e in league_element:
        try:
            if 'Relegation' not in e.text:
                divlinks_dic[e.text] = {'link': e.a['href']}
        except:
            pass

    return divlinks_dic


def teamdic_change_datestrings_to_timedate_objects(dic):
    """
    Changes in a Teamdic the string Date to Datetime obejects for comparision
    :param dic: only a Teamdic
    :return: Teamdic with Datetime obejects
    """
    # creates new list and replaces the datestring with an datetimeobject
    date_team_dic = copy.deepcopy(dic)

    for key in date_team_dic.keys():
        counterjoin = 0
        counterleave = 0
        for i in date_team_dic[key]['join_dates']:
            date_team_dic[key]['join_dates'][counterjoin] = datetime.strptime(
                i, '%a, %d %b %Y %H:%M:%S %z')
            counterjoin += 1

        for i in date_team_dic[key]['leave_dates']:
            date_team_dic[key]['leave_dates'][counterleave] = datetime.strptime(
                i, '%a, %d %b %Y %H:%M:%S %z')
            counterleave += 1
    # pretty.pprint(date_team_dic)
    return date_team_dic


def get_teamlinks_dic_from_group(website):
    """
    Gets all Teamlinks from a Group.
    Action  is mapped to Button 'Scrap League'
    :param website: only the file.
    :return: dic with added Teams to Groups
    """
    # get html
    group_soup = bs4.BeautifulSoup(website.text, features="lxml")

    teamlinks_dic = {}
    league_element = group_soup.select('.league_table td')

    for e in league_element:
        try:
            if e.text:
                teamlinks_dic[e.text.lstrip()] = {'link': e.a['href']}
        except:
            pass

    return teamlinks_dic


def get_teamdic_from_teamlink(website):
    """
    Gets all Player/Teaminfo from a Teamlink.
    Action  is mapped to Button 'Add Players'
    :param website: website from requests with status 200
    :return: team_dic in Form
            {'steam_id': player_steamid, 'join_dates': [], 'leave_dates': [], 'time_in_team': '', 'join_afterSeasonStart': '-', 'leave_afterSeasonStart': '-'}
    """
    # enter when the 99dmg season starts, used to check if player was in the team at season start
    # season10 start: https://csgo.99damage.de/de/news/74090-jetzt-anmelden-fuer-die-99damage-liga
    # 99dmg season 10 started at 28. September 2018 (18: 00 Uhr)
    # use as input               28.09.2018 18:00 +0200

    dmgseasonstart_datetime = datetime.strptime(CONFIG.SEASON_START_DATE_STRING, '%d.%m.%Y %H:%M %z')
    # get html
    team_soup = bs4.BeautifulSoup(website.text, features="lxml")
    # {'steam_id': player_steamid, 'join_dates': [], 'leave_dates': [], 'time_in_team': '', 'join_afterSeasonStart': '-', 'leave_afterSeasonStart': '-'}
    team_dic = {}

    teamlog_elements = team_soup.select('#team_log tr td')
    team_log_dates = teamlog_elements[::4]
    team_log_playernames = teamlog_elements[1::4]
    team_log_actions = teamlog_elements[2::4]
    team_log_targets = teamlog_elements[3::4]

    for i in range(len(team_log_targets)):

        join_leave_date_string = team_log_dates[i].find('span')['title']
        teamlog_playername = team_log_playernames[i].text
        teamlog_action = team_log_actions[i].text
        teamlog_target = team_log_targets[i].text
        if teamlog_playername:
            if '(admin)' not in teamlog_playername:
                team_dic.setdefault(teamlog_playername, {
                    'steam_id': '-', 'join_dates': [], 'leave_dates': [], 'time_in_team': '',
                    'join_afterSeasonStart': False, 'leave_afterSeasonStart': False})
        if teamlog_target:
            team_dic.setdefault(teamlog_target, {
                'steam_id': '-', 'join_dates': [], 'leave_dates': [], 'time_in_team': '',
                'join_afterSeasonStart': False, 'leave_afterSeasonStart': False})

        if (teamlog_action == 'member_join' or teamlog_action == 'create') and teamlog_playername:
            team_dic[teamlog_playername]['join_dates'].append(
                join_leave_date_string)
        if teamlog_action == 'member_leave':
            if ('(admin)' not in teamlog_playername) and teamlog_playername:
                team_dic[teamlog_playername]['leave_dates'].append(
                    join_leave_date_string)
            elif '(admin)' in teamlog_playername and teamlog_target:
                team_dic[teamlog_target]['leave_dates'].append(
                    join_leave_date_string)
        if teamlog_action == 'member_kick':
            if teamlog_target:
                team_dic[teamlog_target]['leave_dates'].append(
                    join_leave_date_string)
        if teamlog_action == 'member_add':
            if teamlog_target:
                team_dic[teamlog_target]['join_dates'].append(
                    join_leave_date_string)

    datetime_team_dic = teamdic_change_datestrings_to_timedate_objects(
        team_dic)

    for key in datetime_team_dic.keys():
        # last_join_date = datetime_team_dic[key]['join_dates'][0]
        # more join dates than leavedates means he is still in the team

        if len(datetime_team_dic[key]['join_dates']) > len(datetime_team_dic[key]['leave_dates']):
            team_dic[key]['time_in_team'] = 'active'  # still in team

        else:
            # gets last join and leave dates, compares
            try:  # exception if a Player was in a Team but never joined #thx 99
                last_join_date = datetime_team_dic[key]['join_dates'][0]
            except:
                break
            last_leave_date = datetime_team_dic[key]['leave_dates'][0]
            time_team = last_leave_date - last_join_date
            # days, hours, minutes
            team_dic[key]['time_in_team'] = (time_team.days, time_team.seconds // 3600, (time_team.seconds // 60) % 60)
        # checks for switch midseason
        for date in datetime_team_dic[key]['join_dates']:
            if date > dmgseasonstart_datetime:
                team_dic[key]['join_afterSeasonStart'] = True
                break
        for date in datetime_team_dic[key]['leave_dates']:
            if date > dmgseasonstart_datetime:
                team_dic[key]['leave_afterSeasonStart'] = True
                break

    # get steamids of active players
    try:
        tables = team_soup.select('table')
        active_team_table = tables[0].select('tr td')

        active_team_playernames = active_team_table[0::3]
        active_team_steamids = active_team_table[2::3]
        for i in range(len(active_team_playernames)):
            # filters out old steamids, remove part, if you want [Log]
            if '[log]' in active_team_steamids[i].text:
                team_dic[active_team_playernames[i].text]['steam_id'] = active_team_steamids[i].text.split('[', 1)[
                                                                            0][:-1]
            else:
                team_dic[active_team_playernames[i].text]['steam_id'] = active_team_steamids[i].text
    except:
        pass

    if len(team_dic) == 0:
        return 'no players, team deleted'
    else:
        return team_dic
