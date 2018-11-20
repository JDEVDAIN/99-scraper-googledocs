# coding=utf-8
import copy
import io
import logging
import random
import requests
import scrap
import json
import scrapProxylistSpys_one
from user_agent import generate_user_agent


def scrap_league_and_div_data(link, delay=0):
    '''
    @param link
        provide 99dmg seasonlink e.g 'https://csgo.99damage.de/de/leagues/99dmg/989-saison-10'
    @param delay
        delays the scraper by amount in sec, recommended is 5-10 sec
        default is 10 sec

    creates Dic of all Divisions and Teams and writes Data to py file as dmgdata
    '''
    divlinks_list = scrap.get_divlinks_dic_from_leaguepage(link)

    league_team_data = copy.deepcopy(divlinks_list)
    amount_divs = len(league_team_data)
    counter = 0
    # 1.6 estimated proxy timeout 2 sec
    est_runtime_min = round((amount_divs * 1.6) / 60)
    print('Estimated runtime: %s Minutes (Delay: %ss)' %
          (est_runtime_min, delay))
    print('Scraping DACH socks5 Proxies from spys.one')
    # scraping proxies from spys.one
    socks5list = scrapProxylistSpys_one.scrape_DACH_D_and_get_only_proxies_list()
    used_proxy = ''
    l_proxy_counter = 0
    for k, v in divlinks_list.items():
        l_proxy_counter += 1
        # user: change value, for faster or slower proxyswitch, if proxy was fast enough, recommended:20
        if l_proxy_counter == 20:
            used_proxy = ''
            l_proxy_counter = 0

        # passing proxies to scrap methode and getting the new proxieslist (removed slow proxies)
        teamlinks_list, socks5list, used_proxy = scrap.get_teamlinks_dic_from_group(v['link'], socks5list, used_proxy)

        counter += 1
        league_team_data[k].update({'Teams': teamlinks_list})
        # prints number, divname and used proxy ip without port
        print('(%s/%s) %s - %s' %
              (str(counter), str(amount_divs), k, str(used_proxy.split(':')[0])))
        # time.sleep(delay) #not needed

    # TODO is it? do not change the filename, is needed for add_teamdata_to_data
    # TODO make changeable in gui
    print('Done Scraping....writing to File....')
    with io.open('teamdata.json', 'w', encoding="utf-8") as file:
        json.dump(league_team_data, file, indent=4)

    print('Done, add Players can now be used')
    # file.write('dmgdata = ' + pprint.pformat(data))


def connect_team(link, proxy):
    """
    Connects to 99Damage site and gets requests website object
    :param link: link to 99Damage team
    :param proxy: proxy used for the connection
    :return: return request object of teampage
    """
    # headers
    # TODO replace
    headers = {
        'User-Agent': generate_user_agent(device_type=("desktop", "smartphone"))}
    proxies = {
        'http': 'socks5://' + proxy,
        'https': 'socks5://' + proxy
    }
    logging.warning('proxy: ' + proxy)
    # user: change timeout, if to many proxies refuse (recommended = 2)
    website = requests.get(link, headers=headers, proxies=proxies, timeout=2)
    website.raise_for_status()
    return website  # requests objects needed for bs4


def add_teamdata_to_data(delay=10):
    '''
    @param delay
        delays the scraper by amount in sec, recommended is 5-10 sec
        default: 10 sec
    NEEDS dicfile from scrap_league_and_div_data()
    '''
    try:
        # TODO if name changed in gui change here as well
        with open('teamdata.json') as json_data:
            f_teamdata = json.load(json_data)
    except FileNotFoundError as err:
        # TODO output on GUI
        print('[ERROR] You need to run the Leaguesraper first    ', err)
        return
    try:
        with open('team_player_data.json', 'x') as json_data:
            json.dump(f_teamdata, json_data, indent=4)

    except FileExistsError:
        print('team_player_data already existing, only adding missing players')

    with open('team_player_data.json') as json_data:
        teamdata = json.load(json_data)
    counter = 0
    est_teams = len(teamdata.keys()) * 8
    est_time_min = round((est_teams * 1.3) / 60)
    print('Estimated Teams: %s  Estimated time: %s Minutes (Delay %ss)' %
          (str(est_teams), str(est_time_min), str(delay)))
    print('Scraping DACH socks5 Proxies from spys.one')
    # scraping proxies from spys.one
    socks5list = scrapProxylistSpys_one.scrape_DACH_D_and_get_only_proxies_list()
    proxy = ''
    last_proxy_counter = 21
    for k, v in teamdata.items():
        print('scraping %s...' % k)
        for ks, vs in teamdata[k]['Teams'].items():
            if 'Players' not in vs.keys():
                last_proxy_counter += 1
                if last_proxy_counter > 20:
                    proxy = random.choice(socks5list)
                    logging.warning('switch proxy')
                    last_proxy_counter = 0
                while True:
                    try:

                        players = scrap.get_teamdic_from_teamlink(connect_team(vs['link'], proxy))
                        break
                    except:  # must be this broad

                        # remove slow proxy
                        socks5list.remove(proxy)
                        logging.warning('timeout: %s removed (proxies left: %s)' % (proxy, len(socks5list)))
                        # if proxy almost empty get more proxies
                        if len(socks5list) <= 3:  # if used any lower value likelihood of repeated Proxy usage to high
                            socks5list = scrapProxylistSpys_one.scrape_DACH_close_countries_and_get_only_proxies_list()
                            logging.warning('Proxylist empty, get new')
                        # logging.warning(socks5list)
                        proxy = random.choice(socks5list)
                        pass

                teamdata[k]['Teams'][ks].update({'Players': players})
            counter += 1
            print('(%s/%s) %s - %s' %
                  (str(counter), str(est_teams), ks, str(proxy.split(':')[0])))
        # after every division write to file,slower can be moved out of for for speed improvment but less stability

        with io.open('team_player_data.json', 'w', encoding="utf-8") as file:
            json.dump(teamdata, file, indent=4)
            print('wrote Data of %s to File' % k)

    print('Done')
